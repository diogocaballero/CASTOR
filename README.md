# Projeto Castor - Monitoramento de Biofeedback

Este projeto faz parte de uma pesquisa de Inicia��o Cient�fica na UFES, focada no desenvolvimento de um rob� assistente para terapia infantil(Castor). O sistema utiliza dados de sensores (via ESP32) para monitorar o engajamento e a proximidade da crian�a durante as sess�es cl�nicas.

## Como Rodar o Sistema
1. Acesse a pasta do projeto:
   \cd Projeto_auto_terapia\
2. Instale as depend�ncias:
   \python -m pip install -r requirements.txt\
3. Inicie o dashboard:
   \python -m streamlit run src/app.py\

## Funcionalidades Atuais
- Dashboard Interativo: Visualiza��o de engajamento (Alto, M�dio, Baixo).
- An�lise Laser: Gr�fico de proximidade entre a crian�a e o rob�.
- Exporta��o de Dados: Gera��o de arquivos CSV com timestamps tratados.
- Notas Cl�nicas: Campo para registro de observa��es da terapeuta.

## Planejamento - Semana 4
Desenvolvimento da An�lise Longitudinal para compara��o de m�ltiplas sess�es do mesmo paciente e identifica��o de padr�es de evolu��o.

---
**Pesquisador:** Diogo Ivan Caballero Otarola  
**Institui��o:** UFES - Universidade Federal do Esp�rito Santo
