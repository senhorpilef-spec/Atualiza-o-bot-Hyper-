import discord
from discord.ext import commands
from groq import Groq
import asyncio
import traceback
import os
import random

# 🔒 Puxando a chave da Groq de forma segura por variável de ambiente
GROQ_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_KEY:
    print("⚠️ AVISO: GROQ_API_KEY não configurada nas variáveis de ambiente! A Aqua não vai funcionar.")


class AquaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 👑 ID EXCLUSIVO DO GERALDÃO (APENAS VOCÊ MANDA)
        self.CRIADOR_ID = 569633804537430036
        
        # 🎲 Respostas aleatórias de negação para não poluir o chat com textos repetidos
        self.respostas_negacao = [
            "Acesso negado. Meus sistemas operacionais respondem exclusivamente ao comando do criador Geraldão.",
            "Operação abortada. Apenas o Geraldão possui autorização de nível mestre para me executar."
        ]
        print("🤖 [AquaCog] Sistema Groq Sem Limites Iniciado para o Geraldão!")

    @commands.Cog.listener()
    async def on_message(self, message):
        # 1. Ignora mensagens enviadas por outros bots
        if message.author.bot:
            return

        # 2. Verificar se a mensagem é um gatilho para a Aqua
        e_gatilho_aqua = False
        if "aqua" in message.content.lower():
            e_gatilho_aqua = True
        elif message.reference and message.reference.message_id:
            try:
                msg_respondida = await message.channel.fetch_message(message.reference.message_id)
                if msg_respondida.author.id == self.bot.user.id:
                    e_gatilho_aqua = True
            except:
                pass

        if not e_gatilho_aqua:
            return

        # 3. Trava Máxima de Segurança por ID de Usuário (Com respostas aleatórias)
        if message.author.id != self.CRIADOR_ID:
            resposta_escolhida = random.choice(self.respostas_negacao)
            await message.reply(resposta_escolhida)
            return

        if not GROQ_KEY:
            await message.reply("Erro: A chave de API da Groq (GROQ_API_KEY) não foi configurada no sistema.")
            return

        # Mostra no Discord que ela está a responder (Modo Chat IA)
        async with message.channel.typing():
            try:
                # Inicializa o cliente da Groq
                client = Groq(api_key=GROQ_KEY)
                
                prompt_sistema = f"""
                Você é a Aqua, uma inteligência artificial administradora integrada diretamente no servidor de Discord.
                O criador supremo Geraldão deu-te a seguinte ordem ou pergunta: "{message.content}"
                
                Sua resposta deve seguir OBRIGATORIAMENTE este formato exato separados por |||:
                
                [TEXTO]
                Sua resposta conversacional curta reconhecendo a ordem do Geraldão.
                |||
                [CODIGO]
                Código em Python puro usando a biblioteca discord.py para executar a ação ou buscar dados no servidor.
                
                Regras cruciais e obrigatórias para o [CODIGO] (Sintaxe Moderna do Discord.py):
                - Não crie funções (não use 'def'). Escreva as linhas de código diretamente, uma abaixo da outra.
                - Você pode usar 'await' diretamente nas linhas.
                - Variáveis nativas disponíveis para você usar diretamente: `message`, `guild`, `bot`, `channel` e `discord`.
                - Para apagar mensagens ou ler o histórico do canal, você OBRIGATORIAMENTE deve usar loops assíncronas, exemplo: `async for msg in channel.history(limit=100):`. Nunca use 'for msg in channel.history'.
                - Para aplicar castigo/timeout em membros, a propriedade correta no discord.py moderno é `member.timed_out_until`. Nunca use 'timeout_until'.
                - Para responder dados solicitados (como quem é o dono ou listar algo), use sempre `await message.reply(sua_resposta)`.
                - Se a ordem exigir modificar múltiplos canais ou cargos (ex: privar canais, apagar cargos), use estruturas de repetição (for) assíncronas de forma limpa.
                - Nunca use blocos de código com markdown (```py) na área [CODIGO].
                """

                # Executa a chamada assíncrona para a Groq usando o super modelo Llama 3.3
                loop = asyncio.get_event_loop()
                chat_completion = await loop.run_in_executor(
                    None, 
                    lambda: client.chat.completions.create(
                        messages=[
                            {
                                "role": "user",
                                "content": prompt_sistema,
                            }
                        ],
                        model="llama-3.3-70b-versatile",
                        temperature=0.1,  # Reduzido para 0.1 para a IA ser mais precisa e técnica nos códigos
                    )
                )

                resposta_completa = chat_completion.choices[0].message.content
                texto_final = ""
                codigo_gerado = ""
                
                if "|||" in resposta_completa:
                    partes = resposta_completa.split("|||")
                    texto_final = partes[0].replace("[TEXTO]", "").strip()
                    codigo_gerado = partes[1].replace("[CODIGO]", "").strip()
                else:
                    texto_final = resposta_completa.strip()

                # Se houver código técnico para executar, roda IMEDIATAMENTE nos bastidores
                if codigo_gerado and codigo_gerado.strip():
                    ambiente_execucao = {
                        "discord": discord,
                        "message": message,
                        "guild": message.guild,
                        "channel": message.channel,
                        "bot": self.bot,
                        "asyncio": asyncio
                    }
                    
                    linhas_codigo = []
                    for linha in codigo_gerado.split('\n'):
                        linhas_codigo.append(f"    {linha}")
                            
                    codigo_final = "async def _executor_direto():\n" + "\n".join(linhas_codigo)
                    
                    try:
                        exec(codigo_final, ambiente_execucao)
                        funcao_assincrona = ambiente_execucao["_executor_direto"]
                        await funcao_assincrona()
                    except Exception as erro_execucao:
                        # 🔇 MODIFICAÇÃO ANTI-POLUIÇÃO: Em vez de mandar aquele texto gigante que quebra o chat,
                        # o bot apenas avisa de forma limpa e discreta e joga o erro real apenas no console interno.
                        print(f"Erro detalhado no código da IA:\n{traceback.format_exc()}")
                        await message.reply("⚠️ Tive uma pequena falha na sintaxe desse comando. Estou ajustando meus parâmetros para tentar novamente de forma inteligente.")
                        return

                # Se for apenas uma conversa, envia o texto conversacional
                if texto_final and texto_final.strip():
                    if not codigo_gerado or "message.reply" not in codigo_gerado:
                        await message.reply(texto_final)
                    
            except Exception as e:
                erro = traceback.format_exc()
                print(f"Erro interno estrutural na Aqua (Groq):\n{erro}")
                await message.reply("❌ Ocorreu um erro estrutural interno. Meus sistemas de processamento foram reiniciados.")


# Função obrigatória para o Discord.py carregar a Cog
async def setup(bot):
    await bot.add_cog(AquaCog(bot))
            
