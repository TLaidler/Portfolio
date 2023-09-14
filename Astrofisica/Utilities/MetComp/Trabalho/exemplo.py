class ajuste:
	def __init__(self,y,x,i,f,p,tol,er = 1):
		self.y = obsy
		self.x = obx
		self.i = valori
		self.f = valorf
		self.p = passo
		self.tol = tolerancia
		self.er = erro
	def mmq(obsy,obsx,valori,valorf,passo,tolerancia):
		itera = 0 
		while (2*abs((valori-valorf)/(valori+valorf))>tolerancia):
			mmq_array = np.zeros(passo) 
			ateste = np.linspace(valori,valorf,passo) 
			for i in range(passo):
				mmq_array[i] = np.sum((obsy-ateste[i]*obsx)**2) 
			idx_min = np.argmin(mmq_array) 
			valori,ajuste,valorf = ateste[idx_min-1:idx_min+2] 
			print ('melhor fit - iter: '+ str(itera)+'='+str(ajuste))
			itera=itera+1
		return ajuste
	def chi_quad(obsy,obsx,erro,valori,valorf,passo,tolerancia):
    		iteracao = 0 
    		while (2*abs((valori-valorf)/(valori+valorf)) > tolerancia):
        		chi2_array = np.zeros(passo) 
        		w_range = np.linspace(valori,valorf,passo)
        		for i in range(passo):
            			chi2_array[i] = np.sum(((obsy-np.sin(w_range[i]*obsx))/erro)**2) 
        		idx_min = np.argmin(chi2_array) 
        		valori,ajuste,valorf = w_range[idx_min-1:idx_min+2] 
       			print('best fit - iter: '+str(iteracao)+' - T = ', 2*np.pi/ajuste)
        		iteracao += 1
    		return ajuste 
