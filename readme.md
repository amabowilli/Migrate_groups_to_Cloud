# How to Use
Rename or copy the "env_template.py" file to "env.py" and populate all fields

Configure python virtual environment and install package dependencies with:

        python3 -m venv venv
        source venv/Scripts/activate  # If using gitbash on Windows
        source venv/bin/activate      # If on linux/mac
        pip3 install -r requirements.txt

Run script with:

        python3 mirror_group_permissions.py