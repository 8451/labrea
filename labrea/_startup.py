from component_logger import ComponentLogger

comp_logger = ComponentLogger()


@comp_logger.autolog
def run():
    pass
