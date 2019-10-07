import document from 'global/document';


const DATA_ACTIVE = 'data-active';
const bool = value => ({
  true: true,
  false: false,
  1: true,
  0: false,
}[value] || false);

export default () => {
  document
    .querySelectorAll('[data-dropdown]')
    .forEach((element) => {
      element.addEventListener('click', () => {
        const active = bool(element.getAttribute(DATA_ACTIVE));
        element.setAttribute(DATA_ACTIVE, !active);
        if (active) {
          element.classList.remove('is-active');
        } else {
          element.classList.add('is-active');
        }
      });
    });
};
