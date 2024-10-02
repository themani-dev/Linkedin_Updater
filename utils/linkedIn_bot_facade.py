class LinkedInBotState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.credentials_set = False
        self.api_key_set = False
        self.job_application_profile_set = False
        self.gpt_answerer_set = False
        self.parameters_set = False
        self.logged_in = False

    def validate_state(self, required_keys):
        for key in required_keys:
            if not getattr(self, key):
                raise ValueError(f"{key.replace('_', ' ').capitalize()} must be set before proceeding.")

class LinkedInBotFacade:
    def __init__(self, login_component):
        self.login_component = login_component
        self.state = LinkedInBotState()
        self.email = None
        self.password = None
        self.parameters = None


    def set_secrets(self, email, password):
        self._validate_non_empty(email, "Email")
        self._validate_non_empty(password, "Password")
        self.email = email
        self.password = password
        self.state.credentials_set = True

    def set_parameters(self, parameters):
        self._validate_non_empty(parameters, "Parameters")
        self.parameters = parameters
        self.apply_component.set_parameters(parameters)
        self.state.parameters_set = True

    def start_login(self):
        self.state.validate_state(['credentials_set'])
        self.login_component.set_secrets(self.email, self.password)
        self.login_component.start()
        self.state.logged_in = True


    def _validate_non_empty(self, value, name):
        if not value:
            raise ValueError(f"{name} cannot be empty.")
