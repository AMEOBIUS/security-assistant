# VS Code Extension

Security Assistant includes a powerful VS Code extension for seamless developer experience.

## ✨ Features

- **Real-time Scanning**: Scans files on save using `security-assistant` CLI.
- **AI-Powered Quick Fixes**: One-click vulnerability remediation using LLM.
- **Integrated Diagnostics**: Security findings in Problems panel.
- **Intelligent Explanations**: Detailed vulnerability information on hover.
- **Status Bar Indicator**: Real-time scan progress and results.

## 🚀 Installation

1. Install `security-assistant` CLI:
   ```bash
   pip install security-assistant
   ```

2. Install extension from VS Code Marketplace:
   [Security Assistant - AI Security Scanner](https://marketplace.visualstudio.com/items?itemName=ameobius.security-assistant-vscode)

## ⚙️ Configuration

Configure the extension in VS Code settings:

| Setting | Default | Description |
|---------|---------|-------------|
| `security-assistant.cliPath` | `security-assistant` | Path to CLI executable |
| `security-assistant.enableRealtime` | `true` | Enable scan on save |
| `security-assistant.debug` | `false` | Enable debug logging |

## 🤖 AI Features

To enable AI features (Quick Fixes, Explanations), configure your LLM provider in your environment:

```bash
export SA_LLM__PROVIDER=nvidia  # or openai, anthropic, ollama
export SA_LLM__API_KEY=your-api-key
export SA_LLM__MODEL=mistralai/devstral-2-123b-instruct-2512
```

## 🛠️ Development

To contribute to the extension:

1. Clone repository
2. Open `security-assistant-vscode` folder
3. Run `npm install`
4. Run `npm run compile`
5. Press `F5` to launch Extension Development Host
