# Contributing

Useful contributions are small, reproducible and testable.

## Good contributions

- installer fixes with the Windows/Docker/n8n versions noted;
- clearer newcomer error messages;
- workflow bugs with sample payloads that contain no private data;
- security improvements;
- agent prompt changes tied to a concrete failure case;
- documentation that removes a manual step.

## Before opening a pull request

Run:

```powershell
python .\scripts\validate_release.py
```

Do not commit `.env`, `runtime/`, real project configuration, prospect/customer data, private memory stores, model files, n8n credential exports or API keys.

Agent additions should prove that a new role is actually distinct. Prefer improving an existing role over creating another persona.
