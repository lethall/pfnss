export namespace main {
	
	export class ImageInfo {
	    fileName: string;
	    w: number;
	    h: number;
	    favor: string;
	
	    static createFrom(source: any = {}) {
	        return new ImageInfo(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.fileName = source["fileName"];
	        this.w = source["w"];
	        this.h = source["h"];
	        this.favor = source["favor"];
	    }
	}

}

