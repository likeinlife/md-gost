use zed::settings::LspSettings;
use zed_extension_api as zed;

struct MarkdownGost;

impl zed::Extension for MarkdownGost {
    fn new() -> Self {
        Self
    }

    fn language_server_command(
        &mut self,
        server: &zed::LanguageServerId,
        worktree: &zed::Worktree,
    ) -> zed::Result<zed::Command> {
        let binary = LspSettings::for_worktree(server.as_ref(), worktree)?.binary;
        let (path, args, env) = binary
            .map(|settings| (settings.path, settings.arguments, settings.env))
            .unwrap_or_default();
        let command = path
            .or_else(|| worktree.which("md-gost"))
            .ok_or_else(|| {
                "Установите md-gost или укажите путь в lsp.md-gost-lsp.binary.path".to_owned()
            })?;

        Ok(zed::Command {
            command,
            args: args.unwrap_or_else(|| vec!["lsp".to_string()]),
            env: env.unwrap_or_default().into_iter().collect(),
        })
    }
}

zed::register_extension!(MarkdownGost);
