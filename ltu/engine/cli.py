import glob
import logging
from multiprocessing.dummy import Pool

import begin
import coloredlogs
from tqdm import tqdm

from client import ModifyClient

logger = logging.getLogger(__name__)


def run_task_mono_thread(action_function, files, action_label, nb_threads=1, offset=0):
    """Run given action on every files, one at a time.
    """
    for file in files[offset:]:
        logger.info("%s: %s" % (action_label, file))
        action_function(file)


def run_task_multi_thread(action_function, files, action_label, nb_threads=2, offset=0):
    """Run given action on every files using a threading pool.
       It uses a progress bar instead of a usual verbose log.
    """
    pool = Pool(processes=nb_threads)
    items = files[offset:]
    pool_iterable = pool.imap_unordered(action_function, items)
    progress_bar_items = tqdm(total=len(items),
                              iterable=pool_iterable,
                              unit='images',
                              desc='{0: <30}'.format(action_label))
    for item in progress_bar_items:
        pass


@begin.start
def ltuengine_process_dir(action, application_key, input_dir, host=None, nb_threads=1, offset=0):
    """
    Parse given directory for images and perform an action [add|delete] on given LTU Engine
    application. Useful to add/delete a batch of images on multiple threads.
    Params:
     - action: Action to perform on folder [add|delete]
     - application_key: LTU Engine application key
     - input_dir: Folder with all needed inputs
     - [host]: server URL that host the application, default is LTU OnDemand. Custom server.
     - [nb_threads]: number of threads
     - [offset]: starting offset
    """
    coloredlogs.install(level='info')
    # process input parameters
    nb_threads = int(nb_threads)
    offset = int(offset)
    files = glob.glob("{}/*".format(input_dir))
    assert files, "No input file found in %s" % input_dir
    # create modify client
    modifyClient = ModifyClient(application_key, server_url=host)
    # get the appropriate function to run the task
    # - run_task_mono_thread will run on 1 thread and show some logs
    # - run_task_multi_thread will run on multiple threads and use a progress bar
    run_task = run_task_mono_thread if nb_threads == 1 else run_task_multi_thread
    # get the action to perform
    if action == "add":
        logger.info("Adding directory %s images into application %s" % (input_dir, application_key))
        run_task(modifyClient.add_image, files, "Adding image", nb_threads, offset)
    elif action == "del":
        logger.info("Deleting directory %s images from application %s" % (input_dir, application_key))
        run_task(modifyClient.delete_image, files, "Deleting image", nb_threads, offset)
    else:
        assert False, "Unknown action"
