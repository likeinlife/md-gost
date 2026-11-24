-- Pandoc Lua filter for md-to-gost:
--   * render ```plantuml blocks and embedded .puml/.iuml files -> PNG or SVG, inline
--       with auto-numbered figure caption "Рисунок N – <caption>"
--   * demote diagram subheaders (contain "Диаграмма"/"модель данных") to bold text
--       (removed from TOC) and reuse their title as the figure caption
--   * number tables labelled by a <!-- #tbl:... --> marker (or a legacy
--       "### Таблица ..." heading) as "Таблица N – <caption>"
--   * number a code block that carries a caption or a #lst: label as
--       "Листинг N – <caption>", pulling its text from file="..." if asked
--   * demote "Выводы по главе" headers to bold text (removed from TOC)
--   * lay every display formula ($$...$$) out as a borderless table row:
--       the formula centred on the page, its number "(N)" flush right
--   * lay the explanation that follows it ("где X — ...") out the same way:
--       "где" in a narrow first column, the definitions aligned in the second
--   * number sections when the work asks for it (number_sections in book.toml)
--   * start one heading on a new page when it carries the class `.page`
--   * resolve [@fig:]/[@tbl:]/[@eq:]/[@lst:] cross-references and [@bib:] citations
--
-- Captions are wrapped in a Div carrying a `custom-style` attribute, so pandoc's
-- docx writer assigns the Word style itself. Nothing downstream has to recognise
-- caption text by its wording.
--
-- Requires PlantUML when the document contains diagrams. The driver resolves
-- either a `plantuml` command or `java -jar plantuml.jar` and passes it in
-- MD2GOST_PLANTUML / MD2GOST_PLANTUML_PREFIX. `shutil.which` on Windows does
-- not see a jar (PATHEXT has no .JAR); the driver scans PATH for one.

local fig_counter = 0
local tbl_counter = 0
local eq_counter = 0
local lst_counter = 0
local last_header_text = nil  -- most recent section title (for figure captions)

-- Cross-reference support.
--   * diagrams labeled inline on the fence:  ```{.plantuml #fig:label caption="..."}
--   * tables labeled via a leading comment:  <!-- #tbl:label Подпись таблицы -->
--   * formulas labeled the same way:         <!-- #eq:label -->
--   * listings labeled on the fence:          ```{.python #lst:label caption="..."}
--   * references in prose:                   [@fig:label] / [@tbl:label] -> bare number,
--                                            [@eq:label] -> "(N)"
local labels = {}              -- "fig:label"/"tbl:label"/"eq:label"/"lst:label" -> number

-- Bibliography support.
--   * sources declared via comment markers: <!-- #bib:key Полный текст источника -->
--   * cited in prose:                       [@bib:key] -> bare bracketed number "[1]"
--   * the reference list is rendered before the appendices in order of first citation.
local bib_defs = {}    -- "bib:key" -> source text (string)
local bib_num = {}     -- "bib:key" -> assigned number (in citation order)
local bib_order = {}   -- list of "bib:key" in citation order

-- Word styles defined in gost_builder.reference. Referenced by name only here; the
-- formatting itself lives in that one place.
local STYLE_FIG_CAPTION = "GOSTImageCaption"
local STYLE_TBL_CAPTION = "GOSTTableCaption"
local STYLE_BIBLIOGRAPHY = "GOSTBibliography"
local STYLE_FORMULA = "GOSTFormula"
local STYLE_FORMULA_NUMBER = "GOSTFormulaNumber"
local STYLE_EXPLANATION = "GOSTExplanation"
local STYLE_LST_CAPTION = "GOSTListingCaption"

local CAPTION_DASH = "\u{2013}"  -- en-dash, per GOST

-- Directory for rendered images. The md-to-gost driver passes an absolute
-- path via MD2GOST_IMG_DIR so embedded images resolve regardless of pandoc's CWD.
local IMG_DIR = os.getenv("MD2GOST_IMG_DIR")
if not IMG_DIR or IMG_DIR == "" then
  error("MD2GOST_IMG_DIR is unset — run this filter through the md-to-gost driver", 0)
end

-- Section numbering, switched on per work by `number_sections` in book.toml.
local NUMBER_SECTIONS = os.getenv("MD2GOST_NUMBER_SECTIONS") == "1"
local IMAGE_FORMAT = os.getenv("MD2GOST_IMAGE_FORMAT") or "png"
local MAX_HEADING_LEVEL = 6

-- Diagrams are written out during the walk and rendered by a single batched
-- plantuml call at the end: JVM startup dominates an invocation-per-diagram loop.
local pending_renders = {}
local pending_plots = {}
local PLOT_PYTHON = os.getenv("MD2GOST_PYTHON") or "python3"
local PLOT_RENDERER = os.getenv("MD2GOST_PLOT_RENDERER")
local PLANTUML_COMMAND = os.getenv("MD2GOST_PLANTUML")
local PLANTUML_PREFIX = os.getenv("MD2GOST_PLANTUML_PREFIX") or ""

local function file_exists(path)
  local f = io.open(path, "r")
  if f then f:close(); return true end
  return false
end

-- pandoc runs with the chapter directory as CWD, so a diagram path written in
-- the text is relative to it; the include below needs an absolute one.
local CWD = pandoc.system.get_working_directory()

local function absolute(path)
  if path:sub(1, 1) == "/" then return path end
  return CWD .. "/" .. path
end

local function write_source(path, code)
  local fh, ioerr = io.open(path, "w")
  if not fh then
    error(string.format("cannot write %s: %s", path, tostring(ioerr)), 0)
  end
  fh:write(code)
  fh:close()
end

-- Queue diagram number `index` for rendering; returns the image path it will
-- produce. Both diagram sources end up here: `code` is the inline fence body,
-- or nil when the diagram comes from an external file given by `include`.
--
-- An external file is included, not copied into the cache: PlantUML resolves a
-- relative `!include` against the directory of the file that spells it out, so
-- a copy would break every include the author wrote. Including a file that
-- carries its own `@start.../@end...` pulls in exactly that block, which makes
-- a complete diagram and a bare `.iuml` fragment work the same way.
local function queue_diagram(index, code, include)
  local base = string.format("diagram_%02d", index)
  local puml_path = IMG_DIR .. "/" .. base .. ".puml"
  local image_path = IMG_DIR .. "/" .. base .. "." .. IMAGE_FORMAT

  if include then
    local path = absolute(include)
    local fh = io.open(path, "r")
    if not fh then
      error(string.format("diagram file not found: %s", include), 0)
    end
    -- Repeat the file's own diagram kind, so @startmindmap & co. survive.
    local kind = fh:read("a"):match("@start(%a+)") or "uml"
    fh:close()
    code = string.format("@start%s\n!include %s\n@end%s", kind, path, kind)
  elseif not code:find("@startuml") then
    code = "@startuml\n" .. code .. "\n@enduml"
  end

  write_source(puml_path, code)
  pending_renders[#pending_renders + 1] =
    { puml = puml_path, image = image_path, base = base }
  return image_path
end

local function queue_plot(index, source, code, extension)
  local base = string.format("plot_%02d", index)
  local source_path = source and absolute(source) or (IMG_DIR .. "/" .. base .. extension)
  local image_path = IMG_DIR .. "/" .. base .. "." .. IMAGE_FORMAT

  if code then
    write_source(source_path, code)
  elseif not file_exists(source_path) then
    error(string.format("plot file not found: %s", source), 0)
  end
  pending_plots[#pending_plots + 1] = { source = source_path, image = image_path, base = base }
  return image_path
end

-- Dash byte sequences for safe UTF-8 pattern matching in Lua.
local EMDASH = "\226\128\148"  -- U+2014
local ENDASH = "\226\128\147"  -- U+2013

-- Strip a leading "N.", "N.N.", "N.N.N." numeric prefix from header text.
local function strip_num_prefix(s)
  s = s:gsub("^%s*", "")
  -- Repeatedly remove "<digits>." groups, then trailing space.
  while true do
    local ns = s:gsub("^%d+%.%s*", "")
    if ns == s then break end
    s = ns
  end
  return s
end

local function header_text(el)
  return pandoc.utils.stringify(el)
end

local APPENDIX_LETTERS = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
local APPENDIX_PREFIX = "^([^ ]+) (..)%. ()[^ ]"

local function appendix_label(el)
  if el.level ~= 1 then return nil end
  -- The designation is one Cyrillic letter (two UTF-8 bytes).
  local word, letter, title_at = header_text(el):match(APPENDIX_PREFIX)
  if word and pandoc.text.upper(word) == "ПРИЛОЖЕНИЕ"
      and APPENDIX_LETTERS:find(pandoc.text.upper(letter), 1, true) then
    return word, letter, title_at
  end
end

local function is_appendix(el)
  return appendix_label(el) ~= nil
end

-- Bold paragraph helper (keeps text visible, out of TOC).
local function bold_para(text)
  return pandoc.Para({ pandoc.Strong({ pandoc.Str(text) }) })
end

-- Blocks wrapped so that pandoc's docx writer assigns them a Word style.
local function styled_div(blocks, style)
  return pandoc.Div(blocks, pandoc.Attr("", {}, { ["custom-style"] = style }))
end

-- A caption paragraph that carries its Word style explicitly.
local function styled_para(text, style)
  return styled_div({ pandoc.Para({ pandoc.Str(text) }) }, style)
end

-- The shape every figure ends up as: the picture, then its numbered caption.
local function figure_blocks(picture, caption)
  return {
    pandoc.Para({ picture }),
    styled_para(
      string.format("Рисунок %d %s %s", fig_counter, CAPTION_DASH, caption),
      STYLE_FIG_CAPTION),
  }
end

-- Register a label -> number mapping, failing the build on duplicates.
local function register_label(id, number)
  if id == nil or id == "" then return end
  if labels[id] ~= nil then
    error(string.format("Duplicate cross-reference label: #%s", id), 0)
  end
  labels[id] = tostring(number)
end

-- Rewrite a "Глава N. Название" heading as "N. Название".
--
-- Works on the inline list instead of the stringified heading: only the leading
-- inlines that spell out the "Глава N." prefix are replaced, so emphasis, links
-- or non-breaking spaces in the title survive instead of being flattened into
-- a single Str.
local CHAPTER_WORD = "Глава"
local CHAPTER_PREFIX = "^%s*" .. CHAPTER_WORD .. "%s+(%d+)%.%s*()"

-- Can `acc` still grow into the "Глава ..." prefix, or is this heading simply
-- not a chapter heading? Lets the scan stop at the first inline that rules it out.
local function may_be_chapter_prefix(acc)
  local t = acc:gsub("^%s*", "")
  if t == "" then return true end
  if #t < #CHAPTER_WORD then
    return CHAPTER_WORD:sub(1, #t) == t
  end
  return t:sub(1, #CHAPTER_WORD) == CHAPTER_WORD
end

local function strip_chapter_prefix(inlines)
  local acc = ""
  for i = 1, #inlines do
    acc = acc .. pandoc.utils.stringify(inlines[i])
    local num, rest_at = acc:match(CHAPTER_PREFIX)
    if num then
      local out = pandoc.List({ pandoc.Str(num .. ".") })
      -- Text that shared the last consumed inline with the prefix, e.g. the
      -- "Название" half of a single Str("1. Название").
      local leftover = acc:sub(rest_at)
      if leftover ~= "" then
        out:insert(pandoc.Space())
        out:insert(pandoc.Str(leftover))
      end
      for j = i + 1, #inlines do
        out:insert(inlines[j])
      end
      return out
    end
    if not may_be_chapter_prefix(acc) then return nil end
  end
  return nil
end

-- Images written as Pandoc image links get the same auto-numbered
-- "Рисунок N – ..." treatment and fig: labels as inline ```plantuml blocks:
--   ![Caption text](img/photo.png){#fig:label}     raster, embedded as is
--   ![Caption text](img/scheme.puml){#fig:label}   PlantUML source, rendered
--   ![Caption text](img/plot.py){#fig:label}       Python plot source, rendered
-- Caption precedence: caption="..." attr, then alt text, then the nearest
-- section title.
local function is_image_src(src)
  local lower = src:lower()
  return lower:match("%.png$") ~= nil or lower:match("%.jpe?g$") ~= nil
    or lower:match("%.svg$") ~= nil
end

local function is_puml_src(src)
  local lower = src:lower()
  return lower:match("%.puml$") ~= nil or lower:match("%.iuml$") ~= nil
end

local function is_plot_src(src)
  local lower = src:lower()
  return lower:match("%.py$") ~= nil or lower:match("%.idef0$") ~= nil
end

-- Find the first image we handle anywhere inside a block list.
local function first_figure_image(blocks)
  local found = nil
  pandoc.walk_block(pandoc.Div(blocks), {
    Image = function(im)
      if not found and (is_image_src(im.src) or is_puml_src(im.src)
          or is_plot_src(im.src)) then found = im end
    end,
  })
  return found
end

-- Turn an image link into a numbered figure. `identifier` is where the label
-- sits, which differs between the two shapes pandoc produces: on the Figure
-- block with alt text, on the Image itself without it. Returns nil for a source
-- we do not handle (an icon inside prose, a remote URL), leaving it untouched.
local function image_figure(img, identifier)
  local puml = is_puml_src(img.src)
  local plot = is_plot_src(img.src)
  if not puml and not plot and not is_image_src(img.src) then return nil end

  fig_counter = fig_counter + 1
  if identifier and identifier:match("^fig:") then
    register_label(identifier, fig_counter)
  end

  local src = img.src
  if puml then
    src = queue_diagram(fig_counter, nil, img.src)
  elseif plot then
    src = queue_plot(fig_counter, img.src, nil)
  end

  local cap = img.attributes and img.attributes.caption
  if not cap or cap == "" then
    cap = pandoc.utils.stringify(img.caption)
  end
  if cap == "" then
    cap = last_header_text or "Рисунок"
  end

  -- A bare image (no pandoc-native figure caption) plus our numbered caption
  -- paragraph, matching the shape ```plantuml blocks produce.
  return figure_blocks(pandoc.Image({}, src, "", img.attr), cap)
end

-- Legacy table-caption heading: "### Таблица ... – Подпись". Restricted to
-- level 3+ so an ordinary section titled "Таблица ..." is not swallowed.
local function is_table_caption_header(el)
  return el.t == "Header" and el.level >= 3
      and pandoc.utils.stringify(el):match("^%s*Таблица")
end

-- `{.page}` asks for a new page. Pandoc drops heading classes, so the request
-- travels as an empty paragraph; post-processing moves the break onto the
-- heading and deletes the marker. A demoted heading is no longer a section.
local PAGE_BREAK_MARKER =
  '<w:p><w:pPr><w:pStyle w:val="GOSTPageBreak"/></w:pPr></w:p>'

local function finish_header(el, result)
  if not el.classes:includes("page") then
    return result
  end
  local header = result or el
  if header.t ~= "Header" then
    return result
  end
  return { pandoc.RawBlock("openxml", PAGE_BREAK_MARKER), header }
end

function Header(el)
  -- Table-caption headings are numbered in Blocks, in document order alongside
  -- marker-labelled tables. Leave them untouched here.
  if is_table_caption_header(el) then return finish_header(el, nil) end

  local txt = header_text(el)

  -- Drop "Глава N." prefix from chapter headings -> "N. Title".
  if el.level == 1 then
    local rewritten = strip_chapter_prefix(el.content)
    if rewritten then
      el.content = rewritten
      return finish_header(el, el)
    end
  end

  -- Track every section title as caption candidate for the next figure.
  last_header_text = strip_num_prefix(txt)

  -- Appendix titles stay as Heading 1 even if they name a diagram.
  if is_appendix(el) then return finish_header(el, nil) end

  -- Diagram subheaders -> demote to bold (out of TOC); title already captured.
  if txt:match("Диаграмма") or txt:match("[Мм]одель данных") then
    return finish_header(el, bold_para(last_header_text))
  end

  return finish_header(el, nil)
end

-- Capture bold paragraph text as caption candidate for the next figure.
-- This supports the pattern: **Bold title.** followed by a diagram without caption attr.
-- An image alone in a paragraph is a figure and is numbered here: pandoc only
-- wraps it in a Figure block when it carries alt text, so
-- `![](scheme.puml){#fig:x caption="..."}` arrives as a plain Para.
function Para(el)
  if #el.content ~= 1 then return nil end
  local only = el.content[1]

  if only.t == "Strong" then
    last_header_text = strip_num_prefix(pandoc.utils.stringify(only))
    return nil
  end
  if only.t == "Image" then
    return image_figure(only, only.identifier)
  end
  return nil
end

-- Листинг — блок кода, которому автор дал подпись или метку. Код к нему
-- можно приложить двумя способами: набрать прямо в блоке или указать
-- file="path" — тогда блок остаётся пустым, а текст читается из файла.
-- Диапазон строк задаётся отдельным атрибутом lines="10-25".
local LISTING_RANGE = "^(%d+)%s*%-%s*(%d+)$"

local function read_listing(path, range)
  local full = absolute(path)
  local fh = io.open(full, "r")
  if not fh then
    error(string.format("listing file not found: %s", path), 0)
  end
  local text = fh:read("a")
  fh:close()

  if range and range ~= "" then
    local first, last = range:match(LISTING_RANGE)
    if not first then
      error(string.format('listing %s: lines="%s" is not a range like "10-25"', path, range), 0)
    end
    first, last = tonumber(first), tonumber(last)
    if first > last then
      error(string.format("listing %s: lines=\"%s\" ends before it starts", path, range), 0)
    end
    local picked, number = {}, 0
    for line in (text .. "\n"):gmatch("(.-)\n") do
      number = number + 1
      if number >= first and number <= last then picked[#picked + 1] = line end
    end
    if #picked == 0 then
      error(string.format("listing %s: lines %s are past the end of the file", path, range), 0)
    end
    text = table.concat(picked, "\n")
  end

  return (text:gsub("%s+$", ""))
end

local function basename(path)
  return path:match("([^/]+)$") or path
end

function CodeBlock(block)
  local attrs = block.attributes or {}
  local is_plantuml = false
  local plot_extension = nil
  for _, cls in ipairs(block.classes) do
    if cls == "plantuml" then is_plantuml = true break end
    if cls == "plot" then plot_extension = ".py" break end
    if cls == "idef0" then plot_extension = ".idef0" break end
  end

  if plot_extension then
    fig_counter = fig_counter + 1
    local image_path = queue_plot(fig_counter, nil, block.text, plot_extension)
    if block.identifier and block.identifier:match("^fig:") then
      register_label(block.identifier, fig_counter)
    end
    local cap = attrs.caption
    if not cap or cap == "" then cap = last_header_text or "Диаграмма" end
    return figure_blocks(pandoc.Image({}, image_path), cap)
  end

  if not is_plantuml then
    local labelled = block.identifier and block.identifier:match("^lst:")
    local captioned = attrs.caption and attrs.caption ~= ""
    local from_file = attrs.file and attrs.file ~= ""
    -- Неподписанный блок кода остаётся куском текста, а не вложением: под
    -- ГОСТ нумеруется то, на что ссылаются, а служебный фрагмент разметки в
    -- перечень листингов попадать не должен.
    if not (labelled or captioned or from_file) then return nil end

    if from_file then
      if block.text ~= "" then
        error(string.format(
          "listing %s: the fence has both file=\"%s\" and a body — keep one of them",
          block.identifier ~= "" and ("#" .. block.identifier) or attrs.file, attrs.file), 0)
      end
      block.text = read_listing(attrs.file, attrs.lines)
    elseif attrs.lines then
      error('lines="..." works together with file="...": there is nothing to cut', 0)
    end

    lst_counter = lst_counter + 1
    if labelled then register_label(block.identifier, lst_counter) end

    -- Подпись: caption="...", иначе имя файла, иначе заголовок раздела.
    local cap = captioned and attrs.caption
      or (from_file and basename(attrs.file))
      or last_header_text
      or "Листинг"

    return {
      styled_para(
        string.format("Листинг %d %s %s", lst_counter, CAPTION_DASH, cap),
        STYLE_LST_CAPTION),
      block,
    }
  end

  fig_counter = fig_counter + 1
  local image_path = queue_diagram(fig_counter, block.text, nil)

  -- Register a label if one is attached to the fence: ```{.plantuml #fig:label}
  if block.identifier and block.identifier:match("^fig:") then
    register_label(block.identifier, fig_counter)
  end

  -- Caption text precedence: explicit caption="..." attr, then section title.
  local cap = block.attributes and block.attributes.caption
  if not cap or cap == "" then
    cap = last_header_text or "Диаграмма"
  end

  return figure_blocks(pandoc.Image({}, image_path), cap)
end

-- Pandoc 3.x wraps `![alt](src.png){#fig:label}` in a Figure block (identifier
-- on the Figure, alt text in the Figure caption). Convert such figures into the
-- project's "Рисунок N – ..." numbering + fig: cross-ref scheme.
function Figure(el)
  local img = first_figure_image(el.content)
  if not img then return nil end
  return image_figure(img, el.identifier)
end

-- Bibliography source definition: <!-- #bib:key Полный текст источника -->
-- Table markers are left in place here; Blocks pairs them with their table.
function RawBlock(el)
  if el.format ~= "html" then return nil end

  local bkey, btext = el.text:match("^%s*<!%-%-%s*#(bib:%S+)%s*(.-)%s*%-%->%s*$")
  if bkey then
    if bib_defs[bkey] ~= nil then
      error(string.format("Duplicate bibliography definition: #%s", bkey), 0)
    end
    if btext == "" then
      error(string.format("Empty bibliography definition: #%s", bkey), 0)
    end
    bib_defs[bkey] = btext
    return {}  -- drop the comment from output
  end

  return nil
end

local TBL_MARKER = "^%s*<!%-%-%s*#(tbl:%S+)%s*(.-)%s*%-%->%s*$"

local function table_caption(label, text)
  tbl_counter = tbl_counter + 1
  register_label(label, tbl_counter)
  if not text or text == "" then
    text = "Таблица"
  end
  return styled_para(
    string.format("Таблица %d %s %s", tbl_counter, CAPTION_DASH, text),
    STYLE_TBL_CAPTION)
end

local EQ_MARKER = "^%s*<!%-%-%s*#(eq:%S+)%s*(.-)%s*%-%->%s*$"

-- По ГОСТ формула стоит по центру строки, а её номер — у правого поля. Абзац
-- Word выравнивается либо по центру, либо по правому краю, но не так и так
-- сразу, поэтому формула кладётся в строку таблицы без границ. Колонок три:
-- пустая слева уравновешивает колонку с номером, и формула оказывается по
-- центру страницы, а не по центру места, оставшегося от номера.
--
-- Границы снимает gost_builder.postprocess: он узнаёт такую таблицу по стилю
-- GOSTFormula её ячейки, не рисует рамку и не требует подписи «Таблица N».
local NUMBER_COLUMN_WIDTH = 0.12
local FORMULA_COLUMNS = {
  { pandoc.AlignCenter, NUMBER_COLUMN_WIDTH },
  { pandoc.AlignCenter, 1 - 2 * NUMBER_COLUMN_WIDTH },
  { pandoc.AlignRight, NUMBER_COLUMN_WIDTH },
}

-- A formula of its own, i.e. `$$...$$` on its own line. Math left inside a
-- sentence stays where the author put it: it is not numbered and not moved.
local function is_display_math(block)
  return block ~= nil and block.t == "Para" and #block.content == 1
     and block.content[1].t == "Math"
     and block.content[1].mathtype == "DisplayMath"
end

-- The shape every display formula ends up as: one borderless table, whose
-- first row is the formula itself and whose remaining rows, if the author
-- wrote one, are its explanation.
local function formula_table(math, label, rows)
  eq_counter = eq_counter + 1
  register_label(label, eq_counter)
  table.insert(rows, 1, pandoc.Row({
    pandoc.Cell({}),
    pandoc.Cell({ styled_div({ pandoc.Para({ math }) }, STYLE_FORMULA) }),
    pandoc.Cell({ styled_para(string.format("(%d)", eq_counter), STYLE_FORMULA_NUMBER) }),
  }))
  return pandoc.Table(
    pandoc.Caption({}),
    FORMULA_COLUMNS,
    pandoc.TableHead({}),
    { { attr = pandoc.Attr(), body = rows, head = {}, row_head_columns = 0 } },
    pandoc.TableFoot({}))
end

-- Экспликация по ГОСТ: «где» стоит отдельно, а расшифровки символов
-- выровнены по одной вертикали. Это те же колонки, что и у формулы, поэтому
-- экспликация становится продолжением её таблицы, а не таблицей рядом: две
-- смежные таблицы Word склеил бы в одну, а разделительный абзац между ними
-- оторвал бы экспликацию от формулы пустой строкой.
--
-- Пишется она одним абзацем, строки внутри которого разделены переводом
-- строки:
--
--     где $w_i$ — вес i-го критерия;
--     $x_i$ — оценка i-го критерия.
--
-- Распознаётся только сразу за формулой, поэтому абзац прозы, начатый словом
-- «где», в таблицу не превращается.
local EXPLANATION_WORD = "где"

local function starts_explanation(block)
  if block == nil or block.t ~= "Para" then return false end
  local first = block.content[1]
  return first ~= nil and first.t == "Str"
     and (first.text == EXPLANATION_WORD or first.text == "Где")
end

-- Split an inline list on line breaks: one entry per line the author typed.
local function split_lines(inlines)
  local lines, current = {}, {}
  for _, inline in ipairs(inlines) do
    if inline.t == "SoftBreak" or inline.t == "LineBreak" then
      lines[#lines + 1] = current
      current = {}
    else
      current[#current + 1] = inline
    end
  end
  lines[#lines + 1] = current
  return lines
end

-- One explanation line: «где» (only on the first) plus the definition, which
-- spans the formula and number columns so that every definition starts at the
-- same vertical.
local function explanation_row(head, body)
  return pandoc.Row({
    pandoc.Cell(head and { styled_div({ pandoc.Para(head) }, STYLE_EXPLANATION) } or {}),
    pandoc.Cell({ styled_div({ pandoc.Para(body) }, STYLE_EXPLANATION) },
      pandoc.AlignDefault, 1, 2),
  })
end

local function explanation_rows(para)
  local rows = {}
  for index, line in ipairs(split_lines(para.content)) do
    local head = nil
    if index == 1 then
      head = { line[1] }          -- само слово «где»
      table.remove(line, 1)
      while line[1] ~= nil and line[1].t == "Space" do table.remove(line, 1) end
    end
    if #line > 0 then
      rows[#rows + 1] = explanation_row(head, line)
    end
  end
  return rows
end

-- Rows of the explanation that follows the formula at `index`, and how many
-- blocks it took (0 when the formula has none).
local function explanation_after(blocks, index)
  local nxt = blocks[index]
  if not starts_explanation(nxt) then return {}, 0 end
  return explanation_rows(nxt), 1
end

-- Table captions are resolved over the block list rather than per element, so
-- that both supported forms are numbered in document order, and so that a
-- marker which is not directly followed by a table is reported instead of
-- silently attaching itself to some later table.
function Blocks(blocks)
  local out = pandoc.Blocks({})
  local i = 1
  while i <= #blocks do
    local b = blocks[i]
    local consumed = 0

    if b.t == "RawBlock" and b.format == "html" then
      local label, text = b.text:match(TBL_MARKER)
      if label then
        local nxt = blocks[i + 1]
        if not (nxt and nxt.t == "Table") then
          error(string.format(
            "Table marker <!-- #%s ... --> is not immediately followed by a table",
            label), 0)
        end
        out:insert(table_caption(label, text))
        out:insert(nxt)
        consumed = 2
      end
      local eq_label, eq_text = b.text:match(EQ_MARKER)
      if eq_label then
        local nxt = blocks[i + 1]
        if not is_display_math(nxt) then
          error(string.format(
            "Formula marker <!-- #%s --> is not immediately followed by a $$...$$ formula",
            eq_label), 0)
        end
        if eq_text ~= "" then
          error(string.format(
            "Formula marker <!-- #%s --> carries text (%s): a formula has a number, not a caption",
            eq_label, eq_text), 0)
        end
        local rows, trailing = explanation_after(blocks, i + 2)
        out:insert(formula_table(nxt.content[1], eq_label, rows))
        consumed = 2 + trailing
      end
    elseif is_display_math(b) then
      local rows, trailing = explanation_after(blocks, i + 1)
      out:insert(formula_table(b.content[1], nil, rows))
      consumed = 1 + trailing
    elseif is_table_caption_header(b) then
      local txt = pandoc.utils.stringify(b)
      -- Drop any existing "Таблица N.N – " prefix, keep descriptive tail.
      local tail = txt:match(EMDASH .. "%s*(.+)$") or txt:match(ENDASH .. "%s*(.+)$")
      if not tail then
        tail = txt:gsub("^%s*Таблица%s*[%d%.]*%s*", "")
      end
      local label = nil
      if b.identifier and b.identifier:match("^tbl:") then
        label = b.identifier
      end
      out:insert(table_caption(label, tail))
      consumed = 1
    end

    if consumed == 0 then
      out:insert(b)
      consumed = 1
    end
    i = i + consumed
  end
  return out
end

-- Leading arguments of the resolved PlantUML command (`-jar` and the jar path).
local function plantuml_args(tail)
  local args = {}
  if PLANTUML_PREFIX ~= "" then
    for piece in string.gmatch(PLANTUML_PREFIX, "[^\n]+") do
      args[#args + 1] = piece
    end
  end
  for _, piece in ipairs(tail) do
    args[#args + 1] = piece
  end
  return args
end

-- Render every collected diagram in one plantuml run.
local function render_diagrams()
  if #pending_renders == 0 then return end
  if not PLANTUML_COMMAND or PLANTUML_COMMAND == "" then
    error("MD2GOST_PLANTUML is unset — run this filter through the md-to-gost driver", 0)
  end

  local args = plantuml_args({ "-charset", "UTF-8", "-t" .. IMAGE_FORMAT, "-o", IMG_DIR })
  for _, r in ipairs(pending_renders) do
    args[#args + 1] = r.puml
  end

  local ok, err = pcall(pandoc.pipe, PLANTUML_COMMAND, args, "")
  if not ok then
    error("plantuml failed: " .. tostring(err), 0)
  end

  local missing = {}
  for _, r in ipairs(pending_renders) do
    if not file_exists(r.image) then
      missing[#missing + 1] = r.base
    end
  end
  if #missing > 0 then
    error("plantuml rendered no " .. IMAGE_FORMAT .. " for: " .. table.concat(missing, ", "), 0)
  end
end

-- Run optional Matplotlib/Seaborn plots after collecting them in the same
-- figure order used by PlantUML and images.
local function render_plots()
  for _, plot in ipairs(pending_plots) do
    if not PLOT_RENDERER or PLOT_RENDERER == "" then
      error("MD2GOST_PLOT_RENDERER is unset — run this filter through the md-to-gost driver", 0)
    end
    local args = { PLOT_RENDERER, plot.source, plot.image }
    local ok, err = pcall(pandoc.pipe, PLOT_PYTHON, args, "")
    if not ok then
      error("plot rendering failed (see renderer error above): " .. tostring(err), 0)
    end
    if not file_exists(plot.image) then
      error("plot renderer produced no " .. IMAGE_FORMAT .. " for: " .. plot.base, 0)
    end
  end
end

-- Assign a bibliography number on first citation (citation order).
local function bib_cite_number(id)
  if bib_defs[id] == nil then
    error(string.format("Undefined bibliography reference: [@%s]", id), 0)
  end
  if not bib_num[id] then
    table.insert(bib_order, id)
    bib_num[id] = #bib_order
  end
  return bib_num[id]
end

local function is_unnumbered(el)
  for _, cls in ipairs(el.classes) do
    if cls == "unnumbered" then return true end
  end
  return false
end

local function walk_numbered_headings(doc, visit)
  local in_appendix = false
  return doc:walk({
    Header = function(h)
      if h.level == 1 then in_appendix = is_appendix(h) end
      if not in_appendix and not is_unnumbered(h) then return visit(h) end
    end,
  })
end

-- Prefix every numbered heading with its section number: "1", "1.1", "1.1.1".
--
-- The numbering root is the shallowest level that actually gets a number, not
-- level 1. Pandoc's own --number-sections counts absolute levels, which suits
-- the report (chapters are level 1) but turns a lab — where the only level-1
-- heading is the title of the work and sections start at level 2 — into
-- "0.1", "0.1.1". Choosing the root by what is numbered makes both shapes read
-- 1, 1.1, 1.1.1 without rearranging the text.
--
-- Headings marked `{-}` (pandoc's `unnumbered` class) are skipped and do not
-- advance any counter: «Введение», «Заключение» and the generated reference
-- list carry no section number under GOST.
local function number_sections(doc)
  local root = nil
  walk_numbered_headings(doc, function(h)
    if root == nil or h.level < root then root = h.level end
  end)
  if root == nil then return doc end

  local counters = {}
  return walk_numbered_headings(doc, function(h)
    local depth = h.level - root + 1
    counters[depth] = (counters[depth] or 0) + 1
    for deeper = depth + 1, MAX_HEADING_LEVEL do counters[deeper] = nil end

    local parts = {}
    for i = 1, depth do parts[i] = tostring(counters[i] or 0) end
    h.content:insert(1, pandoc.Space())
    h.content:insert(1, pandoc.Str(table.concat(parts, ".")))
    return h
  end)
end

local function insert_bibliography(blocks)
  local position = #blocks + 1
  for index, block in ipairs(blocks) do
    if block.t == "Header" and is_appendix(block) then
      position = index
      break
    end
  end

  local title = pandoc.Header(1, { pandoc.Str("Перечень использованных информационных ресурсов") },
    pandoc.Attr("", { "unnumbered" }))
  local items = {}
  for _, id in ipairs(bib_order) do
    items[#items + 1] = { styled_para(bib_defs[id], STYLE_BIBLIOGRAPHY) }
  end
  blocks:insert(position, title)
  blocks:insert(position + 1, pandoc.OrderedList(items))
end

local function format_appendix_title(block, word, letter, title_at)
  local title = pandoc.Inlines({
    pandoc.Str(word), pandoc.Space(), pandoc.Str(letter), pandoc.LineBreak(),
  })
  local remaining = title_at - 1
  for _, inline in ipairs(block.content) do
    if remaining == 0 then
      title:insert(inline)
    else
      local text = pandoc.utils.stringify(inline)
      if #text > remaining then title:insert(pandoc.Str(text:sub(remaining + 1))) end
      remaining = math.max(0, remaining - #text)
    end
  end
  block.content = title
end

-- Keep the appendix heading in the TOC and pass layout changes to DOCX
-- post-processing separately, since Pandoc drops heading classes.
local function format_appendices(blocks)
  local page = "Body"
  local marked = pandoc.List()
  for _, block in ipairs(blocks) do
    if block.t == "Header" and block.level == 1 then
      local wanted = "Body"
      local word, letter, title_at = appendix_label(block)
      if word then
        local paper = block.attributes.paper == "a3" and "A3" or "A4"
        local orientation = block.classes:includes("landscape") and "Landscape" or "Portrait"
        wanted = paper .. orientation
        format_appendix_title(block, word, letter, title_at)
      end
      if wanted ~= page then
        marked:insert(pandoc.RawBlock("openxml",
          '<w:p><w:pPr><w:pStyle w:val="GOSTSection' .. wanted .. '"/></w:pPr></w:p>'))
        page = wanted
      end
    end
    marked:insert(block)
  end
  return marked
end

-- Resolve [@fig:label]/[@tbl:label] citations to bare numbers. Runs after all
-- element-wise functions, so every label has been collected (forward refs OK).
function Pandoc(doc)
  render_diagrams()
  render_plots()

  local resolved = doc:walk({
    Cite = function(c)
      -- Bibliography citation(s): [@bib:key] / [@bib:a; @bib:b] -> "[1]" / "[1, 2]"
      local all_bib = true
      for _, cit in ipairs(c.citations) do
        if not cit.id:match("^bib:") then all_bib = false break end
      end
      if all_bib and #c.citations > 0 then
        local nums = {}
        for _, cit in ipairs(c.citations) do
          table.insert(nums, tostring(bib_cite_number(cit.id)))
        end
        return pandoc.Str("[" .. table.concat(nums, ", ") .. "]")
      end

      local out = {}
      for _, cit in ipairs(c.citations) do
        local id = cit.id
        if id:match("^fig:") or id:match("^tbl:") or id:match("^eq:") or id:match("^lst:") then
          local num = labels[id]
          if not num then
            error(string.format("Undefined cross-reference: [@%s]", id), 0)
          end
          -- A formula is referred to by its number in brackets — «в формуле (3)»
          -- — while a figure or a table is referred to by the bare number.
          if id:match("^eq:") then num = "(" .. num .. ")" end
          table.insert(out, pandoc.Str(num))
        else
          -- Not one of our refs: leave the original citation text intact.
          return nil
        end
      end
      return out
    end,
  })

  -- A source declared but never cited is dropped from the list; that is usually
  -- a typo in the citation key, so say so rather than failing silently.
  local uncited = {}
  for id in pairs(bib_defs) do
    if not bib_num[id] then
      uncited[#uncited + 1] = id
    end
  end
  if #uncited > 0 then
    table.sort(uncited)
    io.stderr:write("md-to-gost: WARNING — declared but never cited, omitted from "
      .. "the reference list: " .. table.concat(uncited, ", ") .. "\n")
  end

  if #bib_order > 0 then
    insert_bibliography(resolved.blocks)
  end

  if NUMBER_SECTIONS then
    resolved = number_sections(resolved)
  end
  resolved.blocks = format_appendices(resolved.blocks)

  return resolved
end
