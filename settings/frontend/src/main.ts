import './style.css';
import './app.css';

import {LoadImage} from '../wailsjs/go/main/App';

window.loadImage = function () {
    try {
        LoadImage(seq)
            .then((result) => {
                const {fileName, favor} = result;
                imageInfo!.innerText = fileName;
                const im = document.getElementById('logo') as HTMLImageElement;
                if (favor == "width") {
                    im.setAttribute("style", "width: 100%, height: auto")
                } else {
                    im.setAttribute("style", "width: auto, height: 100%")
                }
                im.src = fileName;
                seq++
            })
            .catch((err) => {
                console.error(err);
            });
    } catch (err) {
        console.error(err);
    }
};

document.querySelector('#app')!.innerHTML = `
    <img id="logo" class="logo" onclick="loadImage()">Next image</button>
    <p id="imageInfo"></p>
`;
(document.getElementById('logo') as HTMLImageElement).src = '/Users/leehall/work/git/pfnss/Pictures/2002/10/Unknown Location/2002-10-09_19-10-00-assistancedogsofamerica3.jpg';

let imageInfo = document.getElementById("imageInfo");
let seq = 0;

declare global {
    interface Window {
        loadImage: () => void;
    }
}
