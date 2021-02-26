pyinstaller --onedir \
    --add-data="COPYING;."\
    --add-data="README.md;." \
    --add-data="sample_problems;sample_problems" \
    --add-data="tsumemi\resources;tsumemi\resources" \
    --exclude-module=unittest \
    --exclude-module=test \
    --windowed \
    --name=tsumemi \
    "tsumemi_launcher.py"