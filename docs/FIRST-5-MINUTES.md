# First five minutes

This page assumes you did not build Arc Brain and do not know n8n.

## 1. Double-click the installer

Use `INSTALL-ARC-BRAIN.cmd`.

The installer checks the required programs and asks only for:

- which Ollama model(s) to use;
- the names of your first two projects;
- the folder where Arc can store its local inbox.

If the normal n8n/Postgres/Control Room ports are already occupied, the installer chooses an alternate port automatically. The host bridge is protected with a generated token because n8n must reach it from Docker.

## 2. Complete n8n's owner screen

A new self-hosted n8n instance requires you to create its owner account. The installer opens the correct local n8n address.

After signing in:

1. open **Settings → n8n API**;
2. create an API key;
3. copy it;
4. return to the installer window;
5. paste it into the secure prompt.

Arc uses the key to finish setup. It is not written to `.env` or committed to Git.

## 3. Let setup finish

Arc creates the database credential, imports the supplied workflows, starts the local Control Room and runs n8n's security audit.

## 4. Check the install

Double-click `CHECK-ARC-BRAIN.cmd`. Every core check should say `[OK]`.

## 5. Send the first idea

Run:

```powershell
.\scripts\test_intake.ps1
```

Then open the Control Room URL printed by the installer. You should see the test item move through the bounded proposal loop.

## What you do *not* need on day one

Telegram, MemPalace, cloud LLM APIs, SMTP/email sending and automatic code execution are optional. Do not configure them until the local core is working.
