# Project Confluence spaces (markdown mirrors)

When a project has a Confluence space, pipeline pulls it here with **hierarchy preserved** as nested folders + `.md` files.

- [`DD1/`](./DD1/) — see `DD1/README.md`

```bash
python3 scripts/integrations/cli.py confluence sync-pull --space KEY
```
