# schooly

Once finished the installation of Odoo using this tutorial...: 
http://www.theopensourcerer.com/2014/09/how-to-install-openerp-odoo-8-on-ubuntu-server-14-04-lts/
...
 
## Downloading code

In a terminal type the next commands...

    sudo su - odoo -s /bin/bash
    git clone https://www.github.com/pereerro/schooly --depth 1 --branch master --single-branch
    exit

With an editor, add the path to the schooly modules...

    sudo nano /etc/odoo-server.conf

append ",/opt/odoo/schooly" to line begins with "addons-path="

Restart the Odoo server...

    sudo service odoo-server restart

## Installing dependencies

    sudo apt-get install Xvfb fet
    
## Connect to server

In a WEB navigator, link to http://ip_server:8069

## Evaluating

To evaluate the software, create a new database with demo data check activated
 and install the **"School Teacher Assignation and FET"** 
 in *"Configuration/Modules/Local modules"* menu (without Application filter!).

At the moment we have a Odoo database with activities without teachers, calendar
 or room assigned.

With the module **"School Assignation - Create Data"** 
 into *"Configuration/Local Modules"* the wizard create teachers and rooms enough
 to the automatic planning.

Open the wizard *"Teachers Suitability/Assignation Problem/Create Solutions"* and put
the desired parameters. A scheluded task will revise periodically for the pending
computations.

Brewly we will have the solutions in
 *"Teachers Suitability/Assignation Problem/Teachers Assignation Solutions"*.
 Just we could choose one of them and apply the wizard available for the 
 automatic creation of the seances with a defined day/hour, teacher and room.
