from . import passport_blue


@passport_blue.route('/')
def passport():
    return 'passport'
