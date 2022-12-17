async function createCupcake() {

  const flavor = $form.find("#flavor").val();
  const size = $form.find("#size").val();
  const image = $form.find("#image").val();
  const rating = $form.find("#rating").val();

  // TODO: Validate form on backend

  const response = await axios({
      url: `${BASE_URL}/api/cupcakes`,
      method: "POST",
      data: {
          flavor,
          size,
          image,
          rating
      }
  });

  const data = response.data.cupcake;
  appendToList(data);

  $form.trigger("reset");
}

/** Submit form and display newly added cupcake */

$form.on("submit", function (e) {
  e.preventDefault();
  createCupcake();
});