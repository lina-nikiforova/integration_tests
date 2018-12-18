# -*- coding: utf-8 -*-
import fauxfactory
import pytest
from widgetastic.exceptions import MoveTargetOutOfBoundsException

from cfme import test_requirements
from cfme.common.provider_views import NetworkProvidersView
from cfme.networks.provider.nuage import NuageProvider, NetworkProvider
from cfme.utils.blockers import BZ
from cfme.utils.update import update

pytestmark = [
    pytest.mark.provider([NetworkProvider], scope="module"),
    test_requirements.discovery,
    pytest.mark.ignore_stream('5.8'),
    pytest.mark.meta(blockers=[BZ(1518301, forced_streams=['5.9'])])
]


@pytest.mark.rhel_testing
def test_add_cancelled_validation(request, appliance):
    """Tests that the flash message is correct when add is cancelled.

    Polarion:
        assignee: None
        initialEstimate: None
    """
    collection = appliance.collections.network_providers
    try:
        prov = collection.create(prov_class=NuageProvider, name=None, cancel=True,
                                 validate_credentials=False)
        request.addfinalizer(prov.delete_if_exists)
    except MoveTargetOutOfBoundsException:
        # TODO: Remove once fixed 1475303
        prov = collection.create(prov_class=NuageProvider, name=None, cancel=True,
                                 validate_credentials=False)
    view = prov.browser.create_view(NetworkProvidersView)
    view.flash.assert_success_message('Add of Network Manager was cancelled by the user')


def test_network_provider_add_with_bad_credentials(provider):
    """ Tests provider add with bad credentials

    Metadata:
        test_flag: crud

    Polarion:
        assignee: None
        initialEstimate: None
    """
    default_credentials = provider.default_endpoint.credentials

    # default settings
    if provider.appliance.version < '5.10':
        flash = 'Login failed due to a bad username or password.'
    else:
        flash = 'Login failed due to a bad username, password or unsupported API version.'
    default_credentials.principal = "bad"
    default_credentials.secret = 'notyourday'

    with pytest.raises(Exception, match=flash):
        provider.create(validate_credentials=True)


@pytest.mark.smoke
def test_network_provider_crud(provider, has_no_networks_providers):
    """ Tests provider add with good credentials

    Metadata:
        test_flag: crud

    Polarion:
        assignee: None
        initialEstimate: None
    """
    provider.create()
    provider.validate_stats(ui=True)

    old_name = provider.name
    with update(provider):
        provider.name = fauxfactory.gen_alphanumeric(8)

    with update(provider):
        provider.name = old_name  # old name

    provider.delete(cancel=False)
    provider.wait_for_delete()
