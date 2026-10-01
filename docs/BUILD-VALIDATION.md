# Build Validation

The bundle was statically validated before packaging:

- all Python helper files compile with Python 3.13 syntax checking;
- all n8n workflow files are valid JSON;
- workflow node names/IDs are unique inside each workflow;
- every workflow connection target exists;
- every `$node['...']` expression reference points to a node present in that workflow;
- generated Python cache files were removed before packaging.

Not executable-tested in the packaging environment:

- n8n workflow import/runtime against your exact instance;
- PostgreSQL migration execution against your existing Arc database;
- your exact MemPalace CLI path/write interface;
- Telegram credentials;
- SMTP/Gmail delivery.

Those require your running Windows Arc Brain environment and are covered by the smoke tests in `INSTALL-WINDOWS.md`.
