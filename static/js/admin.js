document.addEventListener('DOMContentLoaded', function() {
  // Initialize Materialize components for admin area
  var tabs = document.querySelectorAll('.tabs');
  if (tabs && window.M && M.Tabs) M.Tabs.init(tabs);

  var selects = document.querySelectorAll('select');
  if (selects && window.M && M.FormSelect) M.FormSelect.init(selects);

  var modals = document.querySelectorAll('.modal');
  if (modals && window.M && M.Modal) M.Modal.init(modals);
});

