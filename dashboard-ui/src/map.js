import window from 'global/window';
import L from 'leaflet';
import MapMarkerIcon from './icons/map-marker.svg';
import MapMarkerPersianPinkIcon from './icons/map-marker-persian-pink.svg';
import MapMarkerMayaBlueIcon from './icons/map-marker-maya-blue.svg';
import MapMarkerLightPastelPurpleIcon from './icons/map-marker-light-pastel-purple.svg';
import MapMarkerLightSalmonIcon from './icons/map-marker-light-salmon.svg';
import MapMarkerMediumAquamarineIcon from './icons/map-marker-medium-aquamarine.svg';
import MapMarkerCoralPinkIcon from './icons/map-marker-coral-pink.svg';


export default () => {
  const colloredMarker = (color) => {
    const icon = L.icon({
      iconUrl: color
        ? ({
          'persian-pink': MapMarkerPersianPinkIcon,
          'maya-blue': MapMarkerMayaBlueIcon,
          'light-pastel-purple': MapMarkerLightPastelPurpleIcon,
          'light-salmon': MapMarkerLightSalmonIcon,
          'medium-aquamarine': MapMarkerMediumAquamarineIcon,
          'coral-pink': MapMarkerCoralPinkIcon,
        })[color]
        : MapMarkerIcon,
      iconSize: [24, 24],
      iconAnchor: [12, 24],
    });
    return icon;
  };

  window.L = L;
  window.colloredMarker = colloredMarker;
};
