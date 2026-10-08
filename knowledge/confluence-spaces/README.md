# Project Confluence spaces (markdown mirrors)

When a project has a Confluence space, pipeline pulls it here with **hierarchy preserved** as nested folders + `.md` files.

```bash
python3 scripts/integrations/cli.py confluence sync-pull --space KEY
# → registry/confluence/spaces/KEY/         (JSON, для push)
# → knowledge/confluence-spaces/KEY/        (MD tree)
```
