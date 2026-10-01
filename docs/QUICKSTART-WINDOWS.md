# Windows Quickstart

This is the shortest supported path for someone who did not build Arc Brain.

## Install prerequisites

Install Docker Desktop, Python 3.11+ and Ollama. Start Docker Desktop and Ollama.

## Run one command

In PowerShell from the extracted Arc Brain folder:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
```

Follow the prompts. If no Ollama model exists, the installer can offer `qwen3.5:9b`.

## The one browser step

The first time n8n starts, create its owner account. Then:

1. open **Settings**;
2. open **n8n API**;
3. create an API key;
4. return to PowerShell;
5. paste the key into the secure prompt.

Arc uses it to finish local setup. It is not saved into Git.

## First test

```powershell
.\doctor.ps1
.\scripts\test_intake.ps1
```

If both succeed, drop a `.txt` or `.md` file into one of the watched project folders created under your Arc data directory.
