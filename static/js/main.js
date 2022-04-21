function setCookie(name, value, expires) {
  if (expires) {
    var date = new Date();
    date.setTime(date.getTime() + (expires*24*60*60*1000));
    expires = "; expires=" + date.toUTCString();
  } else {
    expires = ""
  }
  document.cookie = name + "=" + (value || "")  + expires + "; path=/";
}

function getCookie(name) {
  var nameEQ = name + "=";
  var ca = document.cookie.split(';');
  for(var i=0;i < ca.length;i++) {
    var c = ca[i];
    while (c.charAt(0)==' ') c = c.substring(1,c.length);
    if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
  }
  return null;
}

const url = "https://i.ppga.ml/upload";
var apiKey = document.getElementById("apikey");
var file = document.getElementById("file");

if(apiKey.value == "" && setCookie("apiKey") != "" && setCookie("apiKey") != null && setCookie("apiKey") != undefined) {
  apiKey.value = setCookie("apiKey");
}

function showAlert() {
  Swal.fire({
  	title: "Uploading",
    html: '<p>Loading...</p>',
    timerProgressBar: true,
    allowOutsideClick: false,
    didOpen: () => {
      Swal.showLoading();
    },
  });
}

function showError(text) {
	Swal.close();
  Swal.fire({
    icon: 'error',
    title: 'Error',
    text: text,
    allowOutsideClick: true,
  });
}

function setText(text) {
  b = Swal.getHtmlContainer().querySelector('p');
  b.innerHTML = text;
}

function upload() {
  if(file.files.length == 0) {
    showError("File not selected")
    return;
  }
  showAlert();
  var fd = new FormData();
  fd.append("file", file.files[0]);
  let request = new XMLHttpRequest();
  request.open("POST", url, true);
  request.setRequestHeader("Authorization", `${apiKey.value}`);
  request.onload = function() {
    if (this.status >= 200 && this.status < 400) {
      setCookie("apiKey", apiKey, 7);
      const data = JSON.parse(this.response);
      const url = `https://i.ppga.ml/${data.id}`;
      setText(`File uploaded!<br>Redirecting to <a href="${url}">${url}</a>`);
      location.replace(url);
    } else if (this.status == 401) {
      showError(`Invalid api key!`);
    } else if (this.status == 500) {
      showError(`Server error!`);
    } else {
      showError(`Unknown error code ${this.status}!`);
    }
  }
  request.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 0) {
      showError(`Failed to connect to the server!`);
    }
  }
  setText(`Uploading file...`);
  request.send(fd);
}