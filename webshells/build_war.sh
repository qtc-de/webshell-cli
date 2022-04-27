#!/bin/sh

if ! command -v jar &> /dev/null; then
    echo "[-] Error: Cannot find the jar command on your system."
    exit 1
fi

if ! [[ -f "index.jsp" ]]; then
    echo "[+] Renaming webshell.jsp to index.jsp"
    cp webshell.jsp index.jsp
fi

echo "[+] Bundeling webshell.war file:"
jar -cvf webshell.war index.jsp &> /dev/null

echo "[+] Removing index.jsp file"
rm index.jsp
