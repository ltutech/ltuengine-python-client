import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class Stat(object):
    """Manage the queries and images statistics
    """

    def __init__(self):

        #images
        self.treated = {} #how many images could have been successfully treated per action
        self.treated["add"] = 0
        self.treated["delete"] = 0
        self.treated["search"] = 0

        self.to_treat = 0 #images to treat - offset
        self.queries_to_treat = 0 #complete number of queries
        self.submitted = 0 #images in the repertory - already treated
        self.already = 0 #how many images already treated

        self.nb_errors = {} #how many images failed to be treated
        self.nb_errors["total"] = 0
        self.nb_errors["add"] = 0
        self.nb_errors["delete"] = 0
        self.nb_errors["search"] = 0

        self.time = {}
        self.time["add"] = 1
        self.time["delete"] = 1
        self.time["search"] = 1

    def add_error(self, action):
        """add one more error for one specified action"""
        self.nb_errors[action] += self.nb_errors[action]

    def get_nb_errors(self):
        """return the number of errors"""
        nbe = 0
        for action in self.nb_errors:
            nbe += self.nb_errors[action]
        return nbe

    def get_nb_queries_treated(self):
        """return how manies queries succed"""
        nbq = 0
        for action in self.treated:
            nbq += self.treated[action]
        return nbq

    def set_result_per_action(self, action, end_time):
        """save in a list the result of an action"""
        self.time[action] += end_time
        self.time[action] /= 2

    def print_result_per_action(self, nb_threads):
        """print stat per actions"""
        logger.info("Result per actions called:")
        for action in self.treated:
            if self.treated[action] > 0:
                bench = "%s done: %d images in %f sec on %d threads, %f images per sec, %d failded" % (action, self.treated[action], self.time[action], nb_threads, self.treated[action]/ self.time[action], self.nb_errors[action])
            else:
                bench = "%s done: 0 images, %d failed" % (action, self.nb_errors[action])

            logger.info(bench)

    def print_stat_global(self):
        """print the global statistics"""
        logger.info("")
        logger.info("Queries Statistics: ")
        logger.info("{} images to process".format(self.to_treat))
        logger.info("{} queries have been correctly performed on the {} to treat".format(self.get_nb_queries_treated(), self.queries_to_treat))
        logger.info("{} actions failed to be performed: {} add, {} search and {} delete".format(self.get_nb_errors(), self.nb_errors["add"], self.nb_errors["search"], self.nb_errors["delete"]))
        logger.info("{} actions have been already treated for an image and not forced to be processed again".format(self.already))
