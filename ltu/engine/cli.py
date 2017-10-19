#!/usr/bin/env python

import logging
from multiprocessing.dummy import Pool
import os
import time

import begin
import coloredlogs
from tqdm import tqdm

from client import QueryClient, ModifyClient
from ltu.engine.result import Result


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def get_action_name_from_function(function):
    """return from a function (add_image, search_image, delete_image) the name of the action concerned
    """
    return function.__name__.split('_')[0]

def run_single_task(items):
    """Run given action for one file
    """
    in_file = items[0]["in"]
    action_function = items[1]
    action = get_action_name_from_function(items[1])
    out_file = items[0][action]

    #launch action
    result = action_function(in_file)

    #save the result in a json file
    result.save_json(out_file)
    
def run_task_mono_thread(action_function, files, action_label, force_action=True, nb_threads=1, offset=0):
    """Run given action on every files, one at a time.
    """
    items = ()

    for file in files[offset:]:
        items = (file,action_function)
        print("%s: %s" % (action_label, file["in"]))
        run_single_task(items)

def run_task_multi_thread(action_function, files, action_label, force_action=True, nb_threads=2, offset=0):
    """Run given action on every files using a threading pool.
       It uses a progress bar instead of a usual verbose log.
    """
    pool = Pool(processes=nb_threads)
    items = [(file, action_function) for file in files[offset:]]
    pool_iterable = pool.imap_unordered(run_single_task, items)
    progress_bar_items = tqdm(total=len(items),
                              iterable=pool_iterable,
                              unit='images',
                              desc='{0: <30}'.format(action_label))
    for item in progress_bar_items:
        pass

def generate_action(actions_list, input_dir, force):
    """Generate a list of actions to process per image. For each image are saved:
        - input path of the image
        - out path where save the result for each action to perform
    """

    # create results paths if they don't exist
    # result main repertory: out_result
    out_base_path = os.path.join(os.getcwd(), "out_result")
    if not os.path.exists(out_base_path):
        os.mkdir(out_base_path)

    #create one result folder per action
    for action in actions_list:
        action_path = os.path.join(out_base_path, action)
        if not os.path.exists(action_path):
            os.mkdir(action_path)

    files = []
    b_file = False #indicate if there are files to performed

    for dirpath, _, fnames in os.walk(input_dir):
        #relative path from the input images folder, repertory per repertory
        relativ_path = os.path.relpath(dirpath,input_dir)

        if relativ_path == ".":
            relativ_path = ""

        #create actions repertories
        for action in actions_list:
            complete_path = os.path.join(out_base_path, action, relativ_path)
            if not os.path.exists(complete_path):
                os.mkdir(complete_path)

        for file in fnames:
            # files_path["in"]: input image file path
            # files_path[action]: result json file path per action
            if not file == ".DS_Store": #Exept Mac store file
                b_file = True
                files_path = {}
                b_action = False
                for action in actions_list:
                    json_path = os.path.join(out_base_path, action, relativ_path, file) + ".json"
                    #if the folder don't exist or if the action is forced to be executed
                    #the imge will be processed
                    if not os.path.exists(json_path) or force:
                        b_action = True
                        files_path[action] = json_path
                    else:
                        #the image won't be performed
                        logger.debug("%s action already performed for this file. You can consult the result in the Json file. To generate new result, delete the Json File or force the %s action by adding the --force parameter in the command." %(action, action))

                if b_action:
                    files_path["in"] = os.path.join(dirpath, file)
                    files.append(files_path)

    #if no file to treat
    if not b_file and not files:
        assert files, "No input file found in %s" % input_dir
    elif b_file and not files:
        logger.info ("No new file to process. Delete old results folders or force the treatment by adding the --force parameter in the command.")

    return files

@begin.start
def ltuengine_process_dir(actions: "A list(separate each action by a comma) of actions to execute on a folder: add|delete|search or bench(that performs 'delete,add,search,delete') ",
                          application_key: "LTU Engine application key",
                          input_dir:"Folder with all needed inputs",
                          host:"server URL that hosts the application, default is LTU OnDemand"=None,
                          force:" a boolean to indicate what to do if a request has already been executed: force or not"=False,
                          nb_threads:"a list(separate each action by a comma) of number of threads"="1",
                          offset:"starting offset"=0):
    """
    Parse given directory for images and perform action [add|search|delete] on given LTU Engine
    application. Useful to add/delete a batch of images on multiple threads.

    """
    coloredlogs.install(level='info')
    ## process input parameters
    # get all actions
    if actions == "bench":
        actions = "delete,add,search,delete"
        force = True # for a bench actions are forced to be performed
    actions_list = actions.split(',')
    # get all threads nbr
    all_threads = nb_threads.split(',')
    for i in range(0, len(all_threads)):
        all_threads[i] = int(all_threads[i])
    # other parameters
    offset = int(offset)

    #get input and output files path for each image
    files = []
    files = create_images_paths(actions_list, input_dir, force)

    if files:
        nb_files = len(files) - offset
        # create client
        logger.info("")
        modifyClient = ModifyClient(application_key, server_url=host)
        benchs = []

        for nb_threads in all_threads:
            for action in actions_list:
                logger.info("")
                start_time = time.time()
                # get the appropriate function to run the task
                # - run_task_mono_thread will run on 1 thread and show some logs
                # - run_task_multi_thread will run on multiple threads and use a progress bar
                run_task = run_task_mono_thread if nb_threads == 1 else run_task_multi_thread
                # get the action to perform
                if action == "add":
                    logger.info("Adding directory %s images into application %s" % (input_dir, application_key))
                    run_task(modifyClient.add_image, files, "Adding image", force, nb_threads, offset)
                elif action == "delete":
                    logger.info("Deleting directory %s images from application %s" % (input_dir, application_key))
                    run_task(modifyClient.delete_imagefile, files, "Deleting image", force, nb_threads, offset)
                elif action == "search":
                    logger.info("")
                    queryClient = QueryClient(application_key, server_url=host)
                    logger.info("Searching directory %s images into application %s" % (input_dir, application_key))
                    run_task(queryClient.search_image, files, "Searching image", force, nb_threads, offset)
                else:
                    assert False, "Unknown action"

                end_time = (time.time() - start_time)
                bench = "%s done, %d images, in %f sec on %d threads, %f images per sec" % (action, nb_files, end_time, nb_threads, nb_files/end_time)
                logger.info(bench)
                benchs.append(bench)

        for bench in benchs:
            print(bench)
