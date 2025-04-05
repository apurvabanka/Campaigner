document.addEventListener('DOMContentLoaded', function() {
    const createCampaignBtn = document.getElementById('createCampaignBtn');
    const createAICampaignBtn = document.getElementById('createAICampaign');

    function checkCustomerCount(element) {
        const customerCount = parseInt(element.getAttribute('data-customer-count'));
        if (customerCount === 0) {
            alert('Please add customers before creating a campaign.');
            return false;
        }
        return true;
    }

    if (createCampaignBtn) {
        createCampaignBtn.addEventListener('click', function(e) {
            if (!checkCustomerCount(this)) {
                e.preventDefault();
            }
        });
    }

    if (createAICampaignBtn) {
        createAICampaignBtn.addEventListener('click', function(e) {
            if (!checkCustomerCount(this)) {
                e.preventDefault();
            }
        });
    }
}); 