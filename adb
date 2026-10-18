#!/bin/sh
if [ "$3" = "get" ] 2>/dev/null && [ "$1" = "shell" ]; then
  case "$5" in system_locales) printf '%s' "${MOCK_LOCALES:-null}";; esac
fi
exit 0
