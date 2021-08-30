## Disclaimer
This tool was NOT written by Atlassian developers and is considered a third party tool. This means that this is also NOT supported by Atlassian. We highly recommend you have your team review the script before running to ensure you understand the steps/actions taking place as Atlassian is not responsible for the resulting configuration.

The primary security risk is that the resulting permissions from your server environment may cause your code to be openly available to more users/groups than intended. To ensure the resulting permissions are desired, please review the **ActionOnItems.add_group_global_perms()** function, within the **resources/mirror_operations.py** file, as this is where logic is applied to decide what permissions a given user group should gain based off of the current server configuration.

This script only migrates group permissions and does not replicate individual user permissions for project or repo levels.

## Purpose
This tool is written to allow the mirroring of groups, their user membership and their permissions, from Bitbucket Server/DC to Bitbucket Cloud. It is intended that you first migrate your repositories and users via the [Bitbucket Cloud migration assistant](https://www.atlassian.com/software/bitbucket/migration-assistant) (aka "BCMA") as this will ensure your repos and users exist before this tool can be effectively used.

## How to Use
Rename or copy the "env_template.py" file to "env.py" and populate all fields.

Configure python virtual environment and install package dependencies with the follow commands:

        python3 -m venv venv
        source venv/Scripts/activate  # If using gitbash on Windows
        source venv/bin/activate      # If on linux/mac
        pip3 install -r requirements.txt

Run script with python 3.6+ via:

        python3 mirror_group_permissions.py

## Notes
* Users and groups that already exist within your cloud instance will be counted as successful user/group migrations in the counters included in the output
* Only migrates groups that are actually in use within Bitbucket Server/DC. (any groups that exist in the instance but aren't utilized will be skipped)
* Any groups with "System Admin" or "Admin", within [Server's global permissions](https://confluence.atlassian.com/bitbucketserver/global-permissions-776640369.html), will inherit "admin" level permissions to all existing repos and the config will automatically assign "admin" to newly created repos after the fact via [default group permissions](https://support.atlassian.com/bitbucket-cloud/docs/organize-workspace-members-into-groups/).
* The options for "Create Repositories" and "Administer Workspace", as mentioned in the default group permissions doc above, cannot be assigned via the api, so instead the script will print out a list of the groups that would normally gain these permissions at the end of runtime to allow you to manually complete this last step.
* Works with self-signed SSL server instances or instances where SSL cert chains are potentially missing. (though it may throw a warning at the beginning of runtime)

## Permission Mapping
Permissions will have to be "flattened" as Bitbucket Cloud doesn't have project level permissions currently. To acheieve this flattened permission set, the script will look at 3 different permission levels and apply the highest of the 3 as effective/flattened permisison into your cloud instance.

First, the script looks at Bitbucket's [Global Permissions](https://support.atlassian.com/jira-cloud-administration/docs/manage-global-permissions/) to see if a given group has been assigned "admin" or "system admin" as both of these groups automatically inherit "admin" permissions to all repos/projects. 
Second, the script will look to see what the project and repo permissions are for a specific repo, looking to see if a given group has explicitly been granted a permission (read/write/admin) or not. If a permission has been set, use the highest between the project/repo levels.
Third, look to see if the project/repo has a default permission or is set to public, if so, imply a default of "read" or utilize the default permission.

Once all 3 base line permissions are looked up, compare and find the highest level to be explicitly placed onto the repo within the destination cloud repo.
