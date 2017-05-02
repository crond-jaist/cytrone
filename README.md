# CyTrONE: Integrated Cybersecurity Training Framework

CyTrONE is a cybersecurity training framework that aims to simplify
the training setup process through an approach that integrates
training content and training environment management. CyTrONE is being developed by the Cyber Range Organization and Design
(CROND) NEC-endowed chair at the Japan Advanced Institute of Science
and Technology (JAIST).

An overview of CyTrONE is provided below. Based on input from the training organizer and a training database, CyTrONE uploads the training content to a Learning Management System (LMS) via the helper tool called **cnt2lms**, and also creates the associated training environment via the cyber range instantiation system called **CyRIS**, both developed by CROND. Trainees can then access the LMS to consult the training content, connect to the cyber range to conduct the necessary investigation, and then provide the answers via the LMS.

![CyTrONE Overview](https://github.com/crond-jaist/cytrone/blob/master/cytrone_overview.png)

Next we provide brief information on the prerequisites for running CyTrONE, on how to setup, and on how to use CyTrONE. Please refer to the accompanying User Guide for details.

## Prerequisites

The following steps must be carried out _before_ using CyTrONE:
* Install the Moodle LMS on the host used as training content server; please refer to the relevant documentation for details. https://moodle.org/
* Install cnt2lms training content to LMS converter on the same host
  where Moodle is installed; please refer to the cnt2lms User Guide
  for details. https://github.com/crond-jaist/cnt2lms/
* Install CyRIS cyber range instantiation system on the hosts used for
  cyber range creation; please refer to the CyRIS User Guide for
  details. https://github.com/crond-jaist/cyris/

## Setup

To setup CyTrONE follow the steps below:
1. Extract the CyTrONE archive to the hosts to manage the
training and to run Moodle. The archive includes the following sub-directories:
   * "code/": Framework source code written in Python.
   * "scripts/": Helper scripts for managing and using CyTrONE.
   * "database/": Sample training content for CyTrONE.
2. Configure the helper scripts according to the
actual setup (see the files for details):
   * "start_cytrone.sh", "stop_cytrone.sh": To start and stop CyTrONE modules (and ssh tunnels if a gateway is used).
   * "create_training.sh", "end_training.sh", "get_sessions.sh": To create and end training sessions, as well as get active session information.

Note that the following software is required for running CyTrONE
(these requirements are shared with cnt2lms and CyRIS):
* Python: Currently using version 2.7 on Ubuntu OS.
* PyYAML: Library for handling YAML files (http://pyyaml.org/);
currently using version 3.11.

## Quick Start

We provide next the basic steps necessary for using CyTrONE:

1. Start all the CyTrONE modules.

   $ ./start_cytrone.sh

2. Create a new training session by running the command below and making the required choices. Alternatively, the training choice can be provided as an argument (e.g., "1" for creating a NIST Level 1 training in English).

   $ ./create_training.sh 1

3. Check that training content is displayed for the created training session in the Moodle LMS, and that the corresponding cyber range is accessible.

4. End the training session (assuming the session id is 1).

   $ ./end_training.sh 1

5. Stop all the CyTrONE modules (when training activities are finished).

   $ ./stop_cytrone.sh


## References

For a research background regarding CyTrONE, please refer to the
following paper:
* R. Beuran, C. Pham, D. Tang, K. Chinen, Y. Tan, Y. Shinoda,
"CyTrONE: An Integrated Cybersecurity Training Framework",
International Conference on Information Systems Security and Privacy
(ICISSP 2017), Porto, Portugal, February 19-21, 2017, pp. 157-166.
