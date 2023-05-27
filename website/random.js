async function random(a) {
    const lenresponse = await fetch('/BNDnamegenerator/words/'+a+'/len.txt')
    const len = await lenresponse.text();
    const random = new Uint32Array(1)
    self.crypto.getRandomValues(random);
    num = Math.floor((((Number(random[0])+1)/4294967296)*await len) + 0.5 )
    const response = await fetch('/BNDnamegenerator/words/'+a+'/'+num+'.txt')
    const word = await response.text();
    return word
  }

  


