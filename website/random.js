async function random(a) {
    const lenresponse = await fetch('/BNDnamegenerator/words/'+a+'/len.txt')
    if (!lenresponse.ok) throw new Error('Could not load word list '+a)
    const len = Number(await lenresponse.text())
    const random = new Uint32Array(1)
    self.crypto.getRandomValues(random);
    // files are numbered 0 .. len-1
    const num = Math.floor((random[0] / 4294967296) * len)
    const response = await fetch('/BNDnamegenerator/words/'+a+'/'+num+'.txt')
    if (!response.ok) throw new Error('Could not load word '+num+' of '+a)
    const word = await response.text();
    return word
  }
