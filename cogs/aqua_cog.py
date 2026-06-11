import discord
from discord.ext import commands
from groq import Groq
import asyncio
import traceback
import os
import random
import json
from datetime import timedelta

# 🔒 Puxando a chave da Groq de forma segura por variável de ambiente
GROQ_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_KEY:
    print("⚠️ AVISO: GROQ_API_KEY não configurada nas variáveis de ambiente! A Aqua não vai funcionar.")


class AquaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 👑 ID EXCLUSIVO DO GERALDÃO (APENAS VOCÊ MANDA)
        self.CRIADOR_ID = 569633804537430036
        
        self.respostas_negacao = [
            "Acesso negado. Meus sistemas operacionais respondem exclusivamente ao comando do criador Geraldão.",
            "Operação abortada. Apenas o Geraldão possui autorização de nível mestre para me executar."
        ]
        print("🤖 [AquaCog] Sistema de Funções Administrativas Blindadas Ativado para o Geraldão!")

    # 🛠️ FUNÇÕES ADMINISTRATIVAS NATIVAS (BLINDADAS CONTRA ERROS)
    async def executar_acao_administrativa(self, acao, parametros, message):
        guild = message.guild
        channel = message.channel

        try:
            # 1. APAGAR MENSAGENS / LIMPAR CHAT
            if acao == "limpar_mensagens":
                limite = parametros.get("limite", 100)
                usuario_alvo_id = parametros.get("usuario_id")
                
                def check(m):
                    if usuario_alvo_id:
                        return m.author.id == int(usuario_alvo_id)
                    return True

                # Exclui usando a API nativa de forma limpa e rápida
                deleted = await channel.purge(limit=limite, check=check)
                await channel.send(f"🧹 Faxina concluída! {len(deleted)} mensagens foram removidas do canal.", delete_after=5)
                return True

            # 2. MUTAR / APLICAR TIMEOUT / CASTIGO
            elif acao == "mutar_usuario":
                usuario_id = parametros.get("usuario_id")
                minutos = parametros.get("minutos", 60)
                
                if not usuario_id:
                    return False
                
                membro = guild.get_member(int(usuario_id))
                if membro:
                    tempo = timedelta(minutes=int(minutos))
                    await membro.timed_out_until(discord.utils.utcnow() + tempo, reason="Ordem do Geraldão")
                    await message.reply(f"🤫 O usuário {membro.mention} foi colocado de castigo (timeout) por {minutos} minutos.")
                    return True

            # 3. CRIAR CARGO
            elif acao == "criar_cargo":
                nome_cargo = parametros.get("nome")
                if nome_cargo:
                    novo_cargo = await guild.create_role(name=nome_cargo, reason="Ordem do Geraldão")
                    await message.reply(f"👑 Cargo {novo_cargo.mention} criado com sucesso no servidor!")
                    return True

            # 4. PRIVAR TODOS OS CANAIS
            elif acao == "privar_todos_canais":
                for ch in guild.text_channels:
                    try:
                        # Remove a permissão de enviar mensagens e ler histórico do cargo @everyone
                        await ch.set_permissions(guild.default_role, send_messages=False, read_message_history=False)
                    except:
                        continue
                await message.reply("🔒 Todos os canais de texto do servidor foram trancados e privados!")
                return True

            # 5. DELETAR CARGO
            elif acao == "deletar_cargo":
                nome_cargo = parametros.get("nome")
                if nome_cargo:
                    for role in guild.roles:
                        if role.name.lower() == nome_cargo.lower() and not role.is_default():
                            await role.delete(reason="Ordem do Geraldão")
                            await message.reply(f"🗑️ O cargo '{nome_cargo}' foi completamente apagado.")
                            return True

        except Exception as e:
            print(f"Erro ao rodar ação nativa {acao}: {traceback.format_exc()}")
            await message.reply(f"❌ Falha interna ao tentar executar a ação nativa: `{str(e)}`")
        
        return False

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

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

        if message.author.id != self.CRIADOR_ID:
            await message.reply(random.choice(self.respostas_negacao))
            return

        if not GROQ_KEY:
            await message.reply("Erro: A chave de API da Groq (GROQ_API_KEY) não foi configurada no sistema.")
            return

        async with message.channel.typing():
            try:
                client = Groq(api_key=GROQ_KEY)
                
                # Mencionados ou alvos possíveis para ajudar a IA a capturar IDs corretos
                mencionados_str = ""
                if message.mentions:
                    mencionados_str = ", ".join([f"Nome: {m.name}, ID: {m.id}" for m in message.mentions])

                prompt_sistema = f"""
                Você é a Aqua, a inteligência artificial administradora com poder total do servidor de Discord do Geraldão.
                O Geraldão mandou a seguinte ordem: "{message.content}"
                Usuários mencionados na mensagem atual (use se precisar do ID): [{mencionados_str}]
                
                Sua resposta deve seguir estritamente o formato JSON estruturado abaixo. Não use marcações de bloco como ```json. Responda apenas o texto puro do JSON.
                
                {{
                    "texto": "Sua resposta conversacional curta reconhecendo ou confirmando a ordem do Geraldão.",
                    "executar_acao": true ou false (coloque true se ele pediu para apagar mensagens, mutar/timeout, criar cargo, deletar cargo ou privar canais),
                    "acao": "limpar_mensagens" ou "mutar_usuario" ou "criar_cargo" ou "privar_todos_canais" ou "deletar_cargo" (ou deixe vazio "" se for só conversa),
                    "parametros": {{
                        "limite": 100, (número de mensagens para apagar, se aplicável)
                        "usuario_id": "ID_DO_USUARIO_AQUI", (coloque o ID do usuário alvo se a ordem for mutar ou apagar mensagens de alguém específico)
                        "minutos": 60, (tempo de castigo/timeout se a ordem for mutar)
                        "nome": "nome do cargo" (se a ordem for criar ou deletar um cargo)
                    }}
                }}
                """

                loop = asyncio.get_event_loop()
                chat_completion = await loop.run_in_executor(
                    None, 
                    lambda: client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt_sistema}],
                        model="llama-3.3-70b-versatile",
                        temperature=0.0,  # Força a IA a seguir rigorosamente a estrutura técnica
                    )
                )

                resposta_completa = chat_completion.choices[0].message.content.strip()
                
                # Tratamento para garantir a leitura limpa do JSON
                try:
                    dados = json.loads(resposta_completa)
                except:
                    # Fallback caso a IA use blocos markdown por acidente
                    if "```json" in resposta_completa:
                        resposta_completa = resposta_completa.split("```json")[1].split("```")[0].strip()
                    elif "```" in resposta_completa:
                        resposta_completa = resposta_completa.split("```")[1].split("```")[0].strip()
                    dados = json.loads(resposta_completa)

                texto_final = dados.get("texto", "")
                deve_executar = dados.get("executar_acao", False)
                acao_solicitada = dados.get("acao", "")
                parametros_acao = dados.get("parametros", {})

                # Executa a automação blindada de forma nativa e sem erros de digitação
                sucesso_acao = False
                if deve_executar and acao_solicitada:
                    sucesso_acao = await self.executar_acao_administrative(acao_solicitada, parametros_acao, message)

                # Envia a resposta de texto se não houve uma resposta direta da ação ou se for conversa normal
                if texto_final and not sucesso_acao:
                    await message.reply(texto_final)
                    
            except Exception as e:
                print(f"Erro estrutural interno: {traceback.format_exc()}")
                await message.reply("⚠️ Entendi seu comando, mas houve um problema ao processar a estrutura. Tente reescrever a ordem mencionando o usuário de forma clara.")


# Correção de digitação interna para chamar a função corretamente sem quebras
    async def executar_acao_administrative(self, acao, parametros, message):
        return await self.executar_acao_administrative_corrigida(acao, parametros, message)

    async def executar_acao_administrative_corrigida(self, acao, parametros, message):
        return await self.executar_acao_administrativa(acao, parametros, message)


async def setup(bot):
    await bot.add_cog(AquaCog(bot))
                
