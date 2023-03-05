export namespace main {
	
	export class FileItem {
	    id: number;
	    name: string;
	    ix: number;
	
	    static createFrom(source: any = {}) {
	        return new FileItem(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.id = source["id"];
	        this.name = source["name"];
	        this.ix = source["ix"];
	    }
	}

}

