
# CyTrONE: Integrated Cybersecurity Training Framework

CyTrONE is a cybersecurity training framework that simplifies the
training setup process through an approach that integrates training
content and training environment management. CyTrONE is being
developed by the Cyber Range Organization and Design (CROND)
NEC-endowed chair at the Japan Advanced Institute of Science and
Technology (JAIST).

An overview of CyTrONE is provided below, illustrating the overall
workflow, as well as the interaction with several external modules
that are also developed by CROND. Thus, based on input from an
instructor and information retrieved from a training database, CyTrONE
uploads the training content to a Learning Management System (LMS) via
the helper tool called **CyLMS**, and also creates the associated
training environment via the cyber range instantiation system
**CyRIS**; a third module, named **CyPROM**, can be used to manage the
scenario progression in order to include dynamic elements in the
training activity, such as real-time attacks, etc. As for the
trainees, they can access the LMS to consult the training content,
connect to the cyber range to conduct the necessary investigation, and
provide the answers via the LMS.

![CyTrONE Overview](https://github.com/crond-jaist/cytrone/blob/master/cytrone_overview.png)

While the CyTrONE distribution already includes some sample training
content to get you started, we have also started releasing
independently more training content via the [CROND web
page](https://www.jaist.ac.jp/misc/crond/index-en.html). This
additional content currently consists of a set of CTF (Capture The
Flag) style training questions.

Next we provide brief information on the prerequisites for running
CyTrONE, and on how to setup and use the framework. For details,
please refer to the User Guide made available on the
[releases](https://github.com/crond-jaist/cytrone/releases) page,
which also includes the latest stable version of the software.


## Prerequisites

The following steps must be carried out _before_ using CyTrONE:
* Install the **Moodle** LMS on the host used as training content
  server by referring to the relevant documentation for details:
  https://moodle.org/
* Install the **CyLMS** cybersecurity training support tools for LMS
  on the same host where Moodle is installed by referring to the CyLMS
  User Guide: https://github.com/crond-jaist/cylms/
* Install the **CyRIS** cyber range instantiation system on the hosts
  used for cyber range creation by referring to the CyRIS User Guide:
  https://github.com/crond-jaist/cyris/
* Install the **CyPROM** scenario progression management module, also
  on the hosts used for cyber range creation, by referring to the
  CyPROM User Guide: https://github.com/crond-jaist/cyprom/
* Install the **Web-based UI** for CyTrONE by referring to the
  corresponding User Guide:
  https://github.com/crond-jaist/cytrone-ui-web/


## Setup

To setup CyTrONE, follow the steps below:
1. Download the archive of the latest stable version of the CyTrONE
source code from the
[releases](https://github.com/crond-jaist/cytrone/releases) page
2. Extract the CyTrONE archive to the hosts to manage the training and
to run Moodle; the archive includes the following sub-directories:
   * 'code/': Framework source code written in Python
   * 'scripts/': Helper scripts for managing and using CyTrONE
   * 'database/': Sample training content for CyTrONE
3. Create a configuration file for the helper scripts used to manage
CyTrONE according to your actual setup; for this purpose, use the
provided file 'scripts/CONFIG.dist' as template

Note that the following software is required to run CyTrONE (some of
these requirements are shared with CyLMS and CyRIS):
* Python: Currently using version 2.7 on Ubuntu OS
* PyYAML: Library for handling YAML files
* PassLib: Library for handling passwords


## Quick Start

We provide next the basic steps necessary for using CyTrONE:

1. Start the execution of the CyTrONE framework.

   $ ./start_cytrone.sh

2. Create a new training session by running the command below and
selecting one of the pre-configured menu choices displayed (these
choices can be customized by modifying the script
itself). Alternatively, the web-based UI can be used for this purpose.

   $ ./create_training.sh

3. Information about how to access the created cyber range will be
displayed (and trainees must be provided with the details regarding
the instance allocated to each of them); verify that the cyber range
is accessible and that training content is displayed in the Moodle
LMS. The helper script named 'get_notification.sh' can also be used to
retrieve this information at any time.

4. End the created training session (assuming the session id is
1). Again, the web-based UI can also be used for this purpose.

   $ ./end_training.sh 1

5. Stop the execution of the CyTrONE framework when all the training
sessions were completed.

   $ ./stop_cytrone.sh


## References

For a research background regarding CyTrONE, please refer to the
following paper:

* R. Beuran, D. Tang, C. Pham, K. Chinen, Y. Tan, Y. Shinoda,
  "Integrated Framework for Hands-on Cybersecurity Training: CyTrONE",
  Elsevier Computers & Security, vol. 78C, June 2018, pp. 43-59.

For a list of contributors to this project, please check the file
CONTRIBUTORS included with the source code.
