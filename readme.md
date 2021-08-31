## Disclaimer
This tool was NOT written by Atlassian developers and is considered a third-party tool. This means that this is also NOT supported by Atlassian. We highly recommend you have your team review the script before running it to ensure you understand the steps and actions taking place, as Atlassian is not responsible for the resulting configuration.

The primary security risk is that the resulting permissions from your server environment may cause your code to be openly available to more users/groups than intended. To ensure the resulting permissions are desired, review the **ActionOnItems.add_group_global_perms()** function, within the **resources/mirror_operations.py** file, as this is where logic is applied to decide what permissions a given user group should be granted based on the current server configuration.

This script only migrates group permissions and does not replicate individual user permissions for project or repository levels.

## Purpose
This tool is written to allow the mirroring of groups, their user membership, and their permissions from Bitbucket Server/DC to Bitbucket Cloud. It is intended that you first migrate your repositories and users via the [Bitbucket Cloud migration assistant](https://www.atlassian.com/software/bitbucket/migration-assistant) (aka "BCMA") as this will ensure your repositories and users exist before this tool can be effectively used.

## How to Use
Rename or copy the "env_template.py" file to "env.py" and populate all fields.

Configure a python virtual environment and install package dependencies with the follow commands:

        python3 -m venv venv
        source venv/Scripts/activate  # If using gitbash on Windows
        source venv/bin/activate      # If on linux/mac
        pip3 install -r requirements.txt

Run script with python via:

        python3 mirror_group_permissions.py

Note:
This script was written in python 3.9 (to add f-strings from 3.6 and extended type hinting in 3.9).

## Notes
* Users and groups that already exist within your cloud instance will be counted as successful user/group migrations in the counters included printed output
* Only migrates groups that are actually in use within Bitbucket Server/DC. (any groups that exist in the server instance but aren’t utilized will be skipped)
* Any groups with "System Admin" or "Admin", within [Server's global permissions](https://confluence.atlassian.com/bitbucketserver/global-permissions-776640369.html), will inherit "admin" level permissions to all existing repositories and the config will automatically assign "admin" to newly created repositories after the fact via [default group permissions](https://support.atlassian.com/bitbucket-cloud/docs/organize-workspace-members-into-groups/).
* The options for "Create Repositories" and "Administer Workspace", as mentioned in the default group permissions doc above, cannot be assigned via the api, so instead the script will print out a list of the groups that would normally gain these permissions at the end of runtime to allow you to manually complete this last step.
* Works with self-signed SSL server instances or instances where SSL cert chains are potentially missing. (though it may throw a warning at the beginning of runtime)

## Permission Mapping
Permissions will have to be "flattened" as Bitbucket Cloud doesn't currently have project level permissions. To achieve this flattened permission set, the script will look at 3 different permission levels and apply the highest of the 3 as the effective/flattened permisison into your cloud instance.

First, the script looks at Bitbucket's [Global Permissions](https://support.atlassian.com/jira-cloud-administration/docs/manage-global-permissions/) to see if a given group has been assigned "admin" or "system admin" as both of these groups automatically inherit "admin" permissions to all repositories/projects.
Second, the script will look to see what the project and repository permissions are for a specific repository, looking to see if a given group has explicitly been granted a permission (read/write/admin) or not. If a permission has been set, the script uses the highest between the project/repository levels.
Third, look to see if the project/repository has a default permission or is set to public, if so, the script will imply a default of "read" or utilize the default permission.

Once all 3 base line permissions are looked up, the script will compare and find the highest level to be explicitly placed onto the repository within the destination cloud repository.
