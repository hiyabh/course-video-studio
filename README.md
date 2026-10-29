# course-video-studio

סקיל ל-Claude Code שבונה קורס וידאו מונפש בעברית מסילבוס ועד סרטונים, מסמכים ודף צפייה.
דף ההתקנה: https://hiyabh.github.io/course-video-studio/

## מבנה
- `skill/course-video-studio/` - הסקיל עצמו (SKILL.md, references, scripts, template).
- `pack.py` - אורז את הסקיל ל-`course-video-studio.tar.gz`, שהדף ו-`install.sh` מורידים.
- `index.html`, `install.sh`, `robots.txt` - דף ההתקנה ב-GitHub Pages.

אחרי כל שינוי בסקיל: מעלים את `VERSION`, מריצים `python pack.py`, ומבצעים commit ו-push.
