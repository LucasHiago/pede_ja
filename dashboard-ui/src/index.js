import window from 'global/window';

import './scss/noruh-dashboard.scss';
import './imgs/no-avatar.jpg';

import dropdown from './dropdown';
import map from './map';
import modal from './modal';


(() => {
  dropdown();
  map();
  modal();

  if (typeof window.noruhdashboardready === 'function') {
    window.noruhdashboardready();
  }
})();
