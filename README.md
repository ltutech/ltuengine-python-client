
# LTU Engine - Python Client

## ABOUT THIS CLIENT
Jastec France is a company that provides image recognition as a service.
This Python module is a client that allows you to access the HTTP API to
perform image recognition tasks. For more information on image recognition,
please visit http://www.jastec.fr.


Note that this client cannot be used without a valid application key. Please
contact our support department to get your application key today
(support@jastec.fr).

## INSTALL
The client comes in the form of a multiplatform python package. Although the
package has been tested on linux platforms only, it should run fine under
Windows.

Note that python 2.6.+ or later is required.
To know if python is already installed or to check the version use the following command:
```bash
python --version
```

In first, install virtualenv  by typing the folling command in a terminal:
```bash
sudo apt-get install virtualenv
```

Then, create and activate your dev environment in the project folder.
```bash
cd ltuengine-python-client
virtualenv env
source env/bin/activate
```

The package can be installed along with dependencies by running:
```bash
python setup.py install
```

You can check everything is fine by running the unit tests:
```bash
./ltu/engine/testsunit.py
```

## BASIC USAGE
Adding images to the application is done through the add_image() function of a ModifyClient instance:
```python
my_application_key = "replace by your own key"
from ltu.engine.client import ModifyClient
modify_client = ModifyClient(my_application_key)
print(modify_client.add_image("my_image_id", "/home/user/image.jpg"))
```

Once you have at least one image in your application, you can start making
search queries by using the search_image() function of a  QueryClient instance:
```python
from ltu.engine.client import QueryClient
query_client = QueryClient(my_application_key)
print(query_client.search_image("/home/user/image.jpg"))
```

## ADVANCED USAGE

For advanced usage, please consult the docstrings for each function.

## EXEMPLE
An example is provided to quickly test the ADD, SEARCH and DELETE API functions.
You have to execute the file cli.py by specifing these parameters:
Positional arguments:
  ACTION: add, search, del or bench(test the 3 functions in one action)
  APPLICATION_KEY
  INPUT_DIR

Optional arguments:
  --help                show this help message and exit
  --host HOST, -h HOST  (default:  None)
  --nb-threads NB_THREADS, -n NB_THREADS
                        (default: 1)

Here, an example for the ADD feature. A folder containing 5 images is available in this client: ./data
```bash
python ./ltu/engine/cli.py add application_key ./data -n 4
```

If the parameter host is not specified, the script will hit the LTU OnDemand API.
Otherwise, you can specify your own server by adding the domain name or the IP address after --host.
Don't forget to specify http or https.
```bash
python ./ltu/engine/cli.py add application_key ./data --host http://10.5.20.56 -n 4
python ./ltu/engine/cli.py add application_key ./data --host http://mydomainname.com -n 4
```

## LICENSE
This software is licensed under the terms of the Apache License 2.0. In
particular, you are free to distribute it, modify it and to distribute modified
versions as long as you include the attached NOTICE file with your software.
Read the attached LICENSE file for more information.

## CREDITS & USAGE:
Feel free to use any of the resources provided in this client.

EMAIL: support@jastec.fr
