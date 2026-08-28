import re

def update_readme(filepath, is_arabic):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace the main placeholder
    old_placeholder = "![Dashboard Preview](https://via.placeholder.com/800x400?text=Dashboard+Screenshot+Here)"
    if is_arabic:
        new_placeholder = "![واجهة اللوحة الرئيسية](assets/dashboard.png)"
    else:
        new_placeholder = "![Main Dashboard](assets/dashboard.png)"
        
    content = content.replace(old_placeholder, new_placeholder)

    # Insert terminal image before the Terminal feature
    if is_arabic:
        content = content.replace("#### 💻 1. شاشة طرفية", "![الطرفية الذكية](assets/terminal.png)\n\n#### 💻 1. شاشة طرفية")
        content = content.replace("#### 🤖 2. مدير البوتات", "![مدير البوتات](assets/bots_manager.png)\n\n#### 🤖 2. مدير البوتات")
    else:
        content = content.replace("- 💻 **Persistent Web Terminal:**", "![Smart Terminal](assets/terminal.png)\n\n- 💻 **Persistent Web Terminal:**")
        content = content.replace("- 🤖 **Smart Bots Manager:**", "![Bots Manager](assets/bots_manager.png)\n\n- 🤖 **Smart Bots Manager:**")
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

update_readme('/root/server_panel/README_AR.md', True)
update_readme('/root/server_panel/README.md', False)
