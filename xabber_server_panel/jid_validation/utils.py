from .jid import JID, parse, prep_localpart, prep_host


def validate_jid(value):
    try:
        jid_obj = JID(tuple=parse(value))
    except Exception as e:
        return {'success': False, 'error_message': e}

    if jid_obj.user and jid_obj.host:
        try:
            full_jid = jid_obj.full()
            return {"success": True, "full_jid": full_jid}
        except:
            pass

    return {'success': False, 'error_message': 'Invalid JID.'}


def validate_localpart(value):

    try:
        localpart = prep_localpart(value)
        return {"success": True, "localpart": localpart}
    except Exception as e:
        return {'success': False, 'error_message': e}


def validate_host(value):
    try:
        host = prep_host(value)
        return {"success": True, "host": host}
    except Exception as e:
        return {'success': False, 'error_message': e}