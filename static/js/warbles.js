"use strict";

const PORT = 5000;
const BASE_URL = `http://127.0.0.1:${PORT}/`;

const $likeMsgForms = $("form[data-msg-id]");

async function likeWarble(message_id) {

  const response = await axios({
      url: `${BASE_URL}/api/messages/${message_id}/like`,
      method: "POST",
  });

  console.log(response.data.message);
  // appendToList(data);

  // $form.trigger("reset");
}

/** Submit form and display newly added cupcake */

$likeMsgForms.on("submit", function (e) {
  e.preventDefault();
  const msgId = e.target.dataset.msgId
  const resp = likeWarble(msgId);
})