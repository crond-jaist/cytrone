## Important Notice

### The CROND NEC-endowed chair at JAIST that has originally developed CyTrONE ceased to exist in March 2021, and future development will be carried out by the Cybersecurity Research Lab at JAIST in a [new repository](https://github.com/cyb3rlab/cytrone). The original CyTrONE will not be receiving any future updates, so please switch over to the new version as soon as you are able to do so.


# CyTrONE: Integrated Cybersecurity Training Framework

CyTrONE is a cybersecurity training framework that simplifies the
training setup process through an approach that integrates training
content and training environment management. CyTrONE is being
developed by the Cyber Range Organization and Design
([CROND](https://www.jaist.ac.jp/misc/crond/index-en.html))
NEC-endowed chair at the Japan Advanced Institute of Science and
Technology ([JAIST](https://www.jaist.ac.jp/english/)) in Ishikawa,
Japan.

An overview of CyTrONE is provided below, illustrating the overall
workflow, as well as the interaction with several external modules
also developed by CROND. Thus, based on input from an instructor and
information retrieved from a training database, CyTrONE uploads the
training content to a Learning Management System (LMS) via the helper
tool called **CyLMS**, and creates the associated training environment
via the cyber range instantiation system **CyRIS**; a third module,
named **CyPROM**, can be used to manage the scenario progression in
order to include dynamic elements in the training activity, such as
real-time attacks, etc. As for the trainees, they can access the LMS
to consult the training content, connect to the cyber range to conduct
the necessary investigation, and provide answers also via the LMS.

![CyTrONE Overview](https://github.com/crond-jaist/cytrone/blob/master/cytrone_overview.png)

While the CyTrONE distribution already includes some sample training
content to get you started, we also released independently more
training content via the [CROND web
page](https://www.jaist.ac.jp/misc/crond/achievements-en.html). This
additional content comprises a set of CTF (Capture The Flag) style
questions, as well as a set of questions inspired by the NIST
Technical Guide to Information Security Testing and Assessment.

We have prepared install scripts that can be used to set up the entire
CyTrONE framework, including CyRIS, CyLMS, CyPROM and the Moodle VM,
on a single host. Due to specific differences, separate versions of
the script are available for the [Ubuntu 16.04
LTS](https://gist.github.com/crond-jaist/0f3af8bc31928fc3c03afdbf5c5d3696)
and [Ubuntu 18.04
LTS](https://gist.github.com/crond-jaist/592e5d3f92aaf4cf4e53b341a9d6d3cc)
host operating systems. Alternatively, please refer to the next
information on the prerequisites for running CyTrONE, and on how to
set up and use the framework. More details about CyTrONE are available
in the user guide published on the
[releases](https://github.com/crond-jaist/cytrone/releases) page that
also includes the latest stable version of the software.


## Prerequisites

If manual setup is prefered, such as in the case of employing multiple
cyber range hosts, the following steps must be carried out _before_
using CyTrONE:
* Install the **Moodle** LMS on the host used as training content
  server by referring to the relevant documentation for details:
  https://moodle.org/
* Install the **CyLMS** cybersecurity training support tools for LMS
  on the same host where Moodle is installed by referring to the CyLMS
  User Guide: https://github.com/crond-jaist/cylms/
* Install the **CyRIS** cyber range instantiation system on the hosts
  used for cyber range creation by referring to the CyRIS User Guide:
  https://github.com/crond-jaist/cyris/

The following optional components can also be installed:
* Install the **CyPROM** scenario progression management module, also
  on the hosts used for cyber range creation, by referring to the
  CyPROM User Guide: https://github.com/crond-jaist/cyprom/
* Install the **Web-based UI** for CyTrONE by referring to the
  corresponding user guide:
  https://github.com/crond-jaist/cytrone-ui-web/


## Setup

To set up CyTrONE manually, follow the steps below:
1. Download the archive of the latest stable version of the CyTrONE
source code from the
[releases](https://github.com/crond-jaist/cytrone/releases) page
2. Extract the CyTrONE archive on the host used to manage the training
and to run Moodle; the archive includes the following sub-directories:
   * `code/`: Framework source code written in Python
   * `database/`: Sample training content for CyTrONE
   * `moodle/`: Sample configuration file for CyLMS/Moodle
   * `scripts/`: Helper scripts for managing and using CyTrONE
3. Create a configuration file for the helper scripts used to manage
CyTrONE according to your actual setup; for this purpose, use the
file `scripts/CONFIG.dist` as template

Note that the following software is required to run CyTrONE (some of
these requirements are shared with CyLMS and CyRIS):
* Python: Programming language (currently using v2.7)
* PyYAML: Library for handling YAML files
* PassLib: Library for handling passwords


## Quick Start

Assuming that the entire CyTrONE framework was set up, either via the
install scripts mentioned above or manually, following are the basic
steps necessary to use it:

1. Start the execution of the CyTrONE framework.

   `$ ./start_cytrone.sh`

2. Create a new training session by running the command below and
selecting one of the pre-configured menu choices displayed (these
choices can be customized by modifying the script
itself). Alternatively, the web-based UI can be used for this purpose.

   `$ ./create_training.sh`

3. Information about how to access the created cyber range will be
displayed; verify that the cyber range is accessible and that training
content is displayed in the Moodle LMS. The helper script
`get_notification.sh` can also be used to retrieve this information at
any time. Trainees must be provided with the details regarding the
instance allocated to each of them before each training.

4. End the created training session (assuming the session id is
`1`). Again, the web-based UI can also be used for this purpose.

   `$ ./end_training.sh 1`

5. Stop the execution of the CyTrONE framework when all the training
sessions were completed.

   `$ ./stop_cytrone.sh`


## References

For a research background regarding CyTrONE, please refer to the
following paper:

* R. Beuran, D. Tang, C. Pham, K. Chinen, Y. Tan, Y. Shinoda,
  "Integrated Framework for Hands-on Cybersecurity Training: CyTrONE",
  Elsevier Computers & Security, vol. 78C, June 2018, pp. 43-59.

For a list of contributors to this project, please check the file
CONTRIBUTORS included with the source code.
