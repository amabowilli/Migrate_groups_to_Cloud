## How to Use
Rename or copy the "env_template.py" file to "env.py" and populate all fields

Configure python virtual environment and install package dependencies with:

        python3 -m venv venv
        source venv/Scripts/activate  # If using gitbash on Windows
        source venv/bin/activate      # If on linux/mac
        pip3 install -r requirements.txt

Run script with:

        python3 mirror_group_permissions.py

## Notes
* Users and groups that already exist within your cloud instance will be counted as successful user/group migrations in the counters included in the output
* Only migrates groups that are actually in use within Bitbucket Server/DC.
