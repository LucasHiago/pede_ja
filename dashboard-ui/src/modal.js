import document from 'global/document';


const DATA_TRIGGER = 'modal-trigger';
const DATA_CLOSE = 'modal-close';

export default () => {
  document
    .querySelectorAll(`[data-${DATA_TRIGGER}]`)
    .forEach((triggerElem) => {
      const ref = triggerElem.getAttribute(`data-${DATA_TRIGGER}`);
      const element = document.querySelector(ref);
      const closeElems = element.querySelectorAll(`[data-${DATA_CLOSE}]`);

      const open = () => {
        element.classList.add('is-active');
      };
      const close = () => {
        element.classList.remove('is-active');
      };

      triggerElem.addEventListener('click', open);
      closeElems.forEach((closeElem) => {
        closeElem.addEventListener('click', close);
      });
    });
};
