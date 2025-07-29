odoo.define('custom_website.custom_script', function (require) {
    'use strict';

    const publicWidget = require('web.public.widget');

    publicWidget.registry.CustomWebsite = publicWidget.Widget.extend({
        selector: '#call_api_button',
        events: {
            'click': '_onClickCallApi',
        },

        _onClickCallApi: function () {
            console.log('custom-api-button clicked');
            const url = 'https://api.example.com/data';
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    console.log('Success:', data);
                    alert('API Call Successful! Check console for data.');
                })
                .catch((error) => {
                    console.error('Error:', error);
                    alert('API Call Failed!');
                });
        },
    });
});

