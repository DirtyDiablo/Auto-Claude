# N8N Builder Project

Build high-quality n8n workflows using Claude as an orchestrator with specialized AI agents.

## Overview

This project enables Claude to create professional n8n automation workflows by orchestrating specialized AI agents. Claude acts as a coordinator between architecture and implementation agents, using a two-phase approach to build robust, maintainable workflows.

**Key Features:**
- Two-phase workflow creation (Architect → Builder)
- Access to 2,653+ workflow templates
- 7 specialized n8n skills for guidance
- Incremental building with validation every 3-5 nodes
- Pipeline-oriented design thinking
- Specialized debugging and testing agents

## Quick Start

### Prerequisites

- Node.js (v16+)
- Git
- Claude Code CLI
- N8N cloud instance with API access

### Installation

#### 1. Install n8n Skills

```bash
/plugin install czlonkowski/n8n-skills
```

This installs 7 specialized skills:
- n8n Expression Syntax
- n8n MCP Tools Expert
- n8n Workflow Patterns
- n8n Validation Expert
- n8n Node Configuration
- n8n Code JavaScript
- n8n Code Python

#### 2. Configure MCP Connection

The n8n-mcp server is installed automatically via npx when Claude Code starts. You just need to configure the connection.

Copy the example configuration:

```bash
cp .mcp.json.example .mcp.json
```

Edit `.mcp.json` and add your n8n credentials:

```json
{
  "mcpServers": {
    "n8n-mcp": {
      "command": "npx",
      "args": ["-y", "n8n-mcp"],
      "env": {
        "N8N_API_URL": "https://your-instance.app.n8n.cloud",
        "N8N_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

**Note**: The `.mcp.json` file is git-ignored for security. The `-y` flag automatically accepts the npx prompt.

#### 3. Verify Installation

Check that skills are installed:

```bash
/plugin list
```

You should see all 7 n8n skills listed.

The n8n-mcp server will connect automatically when Claude Code starts.

### Getting Your N8N API Key

1. Log into your n8n cloud instance
2. Go to Settings → API
3. Generate a new API key
4. Copy the key to your `.mcp.json` configuration

## How It Works

### Claude's Role

Claude acts as an **orchestrator**, not a direct builder. Claude coordinates between specialized agents:

1. **n8n-workflow-architect** - Designs workflow architecture
2. **n8n-workflow-builder** - Implements workflows incrementally
3. **n8n-workflow-debugger** - Troubleshoots issues
4. **n8n-webhook-tester** - Tests webhook workflows

### Workflow Development Process

```
User Request
    ↓
[Claude: Requirements Gathering]
    ↓
[Architect Agent: Design Architecture]
    ↓
[Claude: Review with User]
    ↓
[Builder Agent: Incremental Implementation]
    ↓
[Testing/Debugging as needed]
    ↓
[Claude: Deploy & Document]
```

### The Spiral Method

Workflows are built using a four-phase approach:

1. **Discovery & Design** - Research templates, design architecture
2. **Incremental Building** - Build 3-5 nodes at a time with validation
3. **Refinement Loops** - Add features one at a time
4. **Deployment & Monitoring** - Gradual activation with monitoring

### Key Principles

- **Think in Pipelines**: Data flows, not individual nodes
- **Build Incrementally**: Validate every 3-5 nodes
- **Use Agents**: Never build directly, always orchestrate
- **Leverage Templates**: Access 2,653+ proven examples
- **Preserve Stability**: Use partial updates, not full replacements

## Usage Examples

### Building a New Workflow

```
User: "I need a workflow that monitors a webhook and sends data to a database"

Claude:
1. Gathers requirements (what data? which database? error handling?)
2. Invokes n8n-workflow-architect agent with complete requirements
3. Reviews architecture with user
4. Invokes n8n-workflow-builder agent with approved architecture
5. Monitors progress and relays updates
6. Tests and deploys workflow
7. Provides usage documentation
```

### Debugging a Workflow

```
User: "My workflow is failing with errors"

Claude:
1. Invokes n8n-workflow-debugger agent
2. Reviews diagnosis (execution history, error patterns, root cause)
3. Explains findings to user
4. Invokes n8n-workflow-builder to fix issues
5. Validates fixes work correctly
```

### Modifying an Existing Workflow

```
User: "Add email notifications to my workflow"

Claude:
1. Invokes n8n-workflow-architect to design modification
2. Reviews change with user
3. Invokes n8n-workflow-builder with partial update
4. Validates modification preserves existing functionality
5. Tests email notifications
```

## Project Structure

```
N8N Builder/
├── CLAUDE.MD                 # Comprehensive guide for Claude
├── README.md                 # This file
├── .mcp.json                 # MCP server config (git-ignored)
├── .mcp.json.example         # Config template
├── .env.example              # Environment variables template
├── .gitignore                # Security configuration
├── n8n-mcp/                  # MCP server installation
│   ├── dist/                 # Built MCP server
│   ├── src/                  # MCP server source
│   └── package.json          # MCP server dependencies
└── projects/                 # (Created by agents) Architecture docs
```

## Available Skills

The project includes 7 specialized skills that activate contextually:

1. **n8n Expression Syntax** - Learn {{}} expressions and variable access
2. **n8n MCP Tools Expert** - Master MCP server tool usage
3. **n8n Workflow Patterns** - Access 5 proven patterns and 2,653+ templates
4. **n8n Validation Expert** - Understand and resolve validation errors
5. **n8n Node Configuration** - Configure nodes correctly
6. **n8n Code JavaScript** - Write effective JavaScript in Code nodes
7. **n8n Code Python** - Use Python with awareness of limitations

## Documentation

- **[CLAUDE.MD](CLAUDE.MD)** - Comprehensive guide for Claude (read this!)
- **[.mcp.json.example](.mcp.json.example)** - MCP configuration template
- **[.env.example](.env.example)** - Environment variables template

## Security

- `.mcp.json` contains API keys and is git-ignored
- Never commit credentials to version control
- API keys should be kept secure and rotated regularly
- Use read-only API keys when possible

## Troubleshooting

### MCP Server Won't Connect

1. Verify Node.js is installed: `node --version`
2. Check n8n-mcp is built: `cd n8n-mcp && npm run build`
3. Verify API URL and key in `.mcp.json`
4. Check logs in n8n-mcp for errors

### Skills Not Available

1. Verify installation: `/plugin list`
2. Reinstall if needed: `/plugin install czlonkowski/n8n-skills`
3. Restart Claude Code

### Workflows Failing

1. Use n8n-workflow-debugger agent for diagnosis
2. Check execution history in n8n
3. Verify credentials are configured in n8n
4. Review validation errors

## Resources

### Official Documentation

- [n8n Documentation](https://docs.n8n.io)
- [n8n Community](https://community.n8n.io)
- [n8n Workflow Templates](https://n8n.io/workflows)

### Repositories

- [n8n-mcp Server](https://github.com/czlonkowski/n8n-mcp-cc-buildier)
- [n8n Skills](https://github.com/czlonkowski/n8n-skills)

### Support

- [n8n-mcp Issues](https://github.com/czlonkowski/n8n-mcp-cc-buildier/issues)
- [n8n Skills Issues](https://github.com/czlonkowski/n8n-skills/issues)
- [n8n Community Forum](https://community.n8n.io)

## Contributing

This project uses open-source components:

- **n8n-mcp**: MIT License
- **n8n-skills**: MIT License

Contributions to the upstream projects are welcome!

## License

This project configuration is provided as-is for use with Claude Code and n8n.

## Next Steps

1. Complete the installation steps above
2. Read [CLAUDE.MD](CLAUDE.MD) for comprehensive usage guide
3. Try building your first workflow with Claude
4. Explore the 2,653+ available templates
5. Join the n8n community for support and inspiration

## Questions?

- Check [CLAUDE.MD](CLAUDE.MD) for detailed guidance
- Review the n8n documentation
- Ask in the n8n community forum
- Open an issue in the relevant repository

Happy automating!
