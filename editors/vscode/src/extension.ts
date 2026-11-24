import * as vscode from "vscode";
import { LanguageClient, LanguageClientOptions, ServerOptions } from "vscode-languageclient/node";

const CLIENT_ID = "md-gost-lsp";

let client: LanguageClient | undefined;
let generation = 0;
let starting: Promise<void> = Promise.resolve();

function serverOptions(): ServerOptions {
  const config = vscode.workspace.getConfiguration(CLIENT_ID);
  const command = config.get<string>("path")?.trim() || CLIENT_ID;
  const configured = config.get<unknown>("args");
  const args = Array.isArray(configured)
    ? configured.filter((item): item is string => typeof item === "string")
    : [];
  return { command, args };
}

function createClient(): LanguageClient {
  const options: LanguageClientOptions = {
    documentSelector: [{ scheme: "file", language: "markdown" }],
    outputChannelName: CLIENT_ID,
  };
  return new LanguageClient(CLIENT_ID, "Markdown ГОСТ", serverOptions(), options);
}

async function replaceClient(): Promise<void> {
  const current = client;
  const ticket = ++generation;
  client = undefined;
  await current?.stop().catch(() => undefined);
  if (ticket !== generation) {
    return;
  }
  const next = createClient();
  client = next;
  await next.start().catch(() => undefined);
}

function restart(): Promise<void> {
  starting = starting.then(replaceClient, replaceClient);
  return starting;
}

export function activate(context: vscode.ExtensionContext): void {
  context.subscriptions.push(
    vscode.commands.registerCommand(`${CLIENT_ID}.restart`, () => {
      void restart();
    }),
    vscode.workspace.onDidChangeConfiguration((event) => {
      if (
        event.affectsConfiguration(`${CLIENT_ID}.path`) ||
        event.affectsConfiguration(`${CLIENT_ID}.args`)
      ) {
        void restart();
      }
    }),
  );
  void restart();
}

export function deactivate(): Thenable<void> | undefined {
  generation += 1;
  const current = client;
  client = undefined;
  return current?.stop();
}
