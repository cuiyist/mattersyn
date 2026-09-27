import {mountSilverReader} from './silver-reader.mjs';
const host = document.getElementById('silver-catalog');
if (host) await mountSilverReader(host, {url: host.dataset.catalogUrl || null, hideEmpty: host.dataset.hideEmpty === 'true'});
