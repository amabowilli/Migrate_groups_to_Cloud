## Disclaimer
This tool was NOT written by Atlassian developers and is considered a third party tool. This means that this is also NOT supported by Atlassian. We highly recommend you have your team review the script before running to ensure you understand the steps/actions taking place as Atlassian is not responsible for the resulting configuration. 

The primary security risk is that the resulting permissions from your server environment may cause your code to be openly available to more users than intended. To ensure the resulting permissions are desired, please review the resources/mirror_operations ActionOnItems.add_group_global_perms() function as this is where logic is applied to decide what permissions a given user group should gain based off of the current server configuration.

This script only migrates group permissions and does not replicate individual user permissions for project or repo levels.

## Purpose
This tool is written to allow the mirroring of groups, their user membership and their permissions, from Bitbucket Server/DC to Bitbucket Cloud. It is intended that you first migrate your repositories and users via the [Bitbucket Cloud migration assistant](https://www.atlassian.com/software/bitbucket/migration-assistant) (aka "BCMA") as this will ensure your repos and users exist before this tool can be effectively used.

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
* Any groups with "System Admin" or "Admin", within [Server's global permissions](https://confluence.atlassian.com/bitbucketserver/global-permissions-776640369.html), will inherit global admin within all repos. "System Admins" will be granted workspace admin while regular "Admins" will not.
* Works with self-signed SSL server instances (though it may throw a warning at the beginning)
