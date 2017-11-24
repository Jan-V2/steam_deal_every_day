from utils import log, log_return, ROOTDIR
import api_key

api = api_key.get_api()


api.update_status('will i post this to twitter?')
